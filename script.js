$(document).ready(function() {
    const state = {
        rotation: { x: 0, y: 0, z: 0 },
        drag: {
            active: false,
            moved: false,
            startX: 0,
            startY: 0,
            lastX: 0,
            lastY: 0,
        },
        render: {
            inFlight: false,
            queued: false,
            requestId: 0,
        },
        selectedAtomIndex: null,
    };

    loadElements();
    loadMolecules();

    $('#add-element-form').submit(function(e) {
        e.preventDefault();
        const data = {
            elementnumber: $('#element-number').val(),
            elementcode: $('#element-code').val(),
            elementname: $('#element-name').val(),
            color1: $('#color-1').val(),
            color2: $('#color-2').val(),
            color3: $('#color-3').val(),
            elementradius: $('#element-radius').val()
        };

        $.ajax({
            type: 'POST',
            url: '/add',
            data: data,
            success: function() {
                loadElements();
                if ($('#molecule-select').val()) {
                    requestDisplay();
                }
                alert('Element added/updated successfully');
            }
        });
    });

    $('#upload-form').submit(function(e) {
        e.preventDefault();
        const fileInput = $('#sdf-file-input')[0];
        const molName = $('#mol-name-input').val();

        if (fileInput.files.length > 0) {
            const formData = new FormData();
            formData.append('molname', molName);
            formData.append('sdf_file', fileInput.files[0]);

            $.ajax({
                type: 'POST',
                url: '/upload',
                data: formData,
                processData: false,
                contentType: false,
                success: function(res) {
                    resetRotation();
                    state.selectedAtomIndex = null;
                    setSelectionInfo('Click an atom to inspect its neighborhood.');
                    loadMolecules(res.name).done(function() {
                        requestDisplay();
                        loadAnalytics(res.name);
                    });
                    alert('Molecule uploaded successfully');
                },
                error: function(err) {
                    const detail = err.responseText ? `\n${err.responseText}` : '';
                    alert('Upload failed: ' + err.statusText + detail);
                }
            });
        }
    });

    $('#molecule-select').change(function() {
        resetRotation();
        state.selectedAtomIndex = null;
        setSelectionInfo('Click an atom to inspect its neighborhood.');
        requestDisplay();
        loadAnalytics($('#molecule-select').val());
    });

    $('#reset-view-btn').on('click', function() {
        resetRotation();
        requestDisplay();
    });

    bindDragRotate();

    function loadElements() {
        $.getJSON('/elements', function(data) {
            const tableBody = $('#elements-table-body');
            tableBody.empty();
            data.forEach(el => {
                tableBody.append(`
                    <tr>
                        <td>${el[1]}</td>
                        <td>${el[2]}</td>
                        <td>${el[6]}px</td>
                    </tr>
                `);
            });
        });
    }

    function loadMolecules(selectedName = null) {
        return $.getJSON('/molecules', function(data) {
            const select = $('#molecule-select');
            const currentVal = select.val();
            select.empty().append('<option value="">-- Choose one --</option>');
            data.forEach(name => {
                const selected = (name === currentVal) ? 'selected' : '';
                select.append(`<option value="${name}" ${selected}>${name}</option>`);
            });

            if (selectedName && data.includes(selectedName)) {
                select.val(selectedName);
            }
        });
    }

    function resetRotation() {
        state.rotation.x = 0;
        state.rotation.y = 0;
        state.rotation.z = 0;
    }

    function scheduleDisplay() {
        state.render.queued = true;
        requestDisplay();
    }

    function requestDisplay() {
        const molName = $('#molecule-select').val();
        if (!molName) {
            $('#svg-container').html('<p style="color: #64748b;">Select a molecule to view</p>');
            clearHighlights();
            return;
        }

        if (state.render.inFlight) {
            state.render.queued = true;
            return;
        }

        state.render.inFlight = true;
        state.render.queued = false;
        const requestId = ++state.render.requestId;

        $.ajax({
            type: 'POST',
            url: '/display',
            data: {
                name: molName,
                phi_x: Math.round(state.rotation.x),
                phi_y: Math.round(state.rotation.y),
                phi_z: Math.round(state.rotation.z)
            },
            dataType: 'text',
            success: function(svg) {
                if (requestId !== state.render.requestId) {
                    return;
                }
                $('#svg-container').html(svg);
                bindSvgInteractions();
                applySelection();
            },
            error: function(err) {
                const msg = err.responseText || err.statusText;
                $('#svg-container').html(`<p style="color:#ef4444;">Display failed: ${msg}</p>`);
                clearHighlights();
            },
            complete: function() {
                state.render.inFlight = false;
                if (state.render.queued) {
                    requestDisplay();
                }
            }
        });
    }

    function loadAnalytics(molName) {
        if (!molName) {
            setAnalyticsEmpty();
            return;
        }

        $.ajax({
            type: 'POST',
            url: '/analyze',
            data: { name: molName },
            dataType: 'json',
            success: function(stats) {
                $('#stat-formula').text(stats.formula || '-');
                $('#stat-mass').text(`${stats.molar_mass.toFixed(3)} g/mol`);
                $('#stat-atoms').text(stats.atom_count);
                $('#stat-bonds').text(stats.bond_count);
                $('#stat-elements').text(formatCounts(stats.element_counts));
                $('#stat-bond-orders').text(formatBondOrders(stats.bond_order_distribution));
            },
            error: function() {
                setAnalyticsError();
            }
        });
    }

    function setAnalyticsEmpty() {
        $('#stat-formula').text('-');
        $('#stat-mass').text('-');
        $('#stat-atoms').text('-');
        $('#stat-bonds').text('-');
        $('#stat-elements').text('-');
        $('#stat-bond-orders').text('-');
    }

    function setAnalyticsError() {
        $('#stat-formula').text('error');
        $('#stat-mass').text('error');
        $('#stat-atoms').text('error');
        $('#stat-bonds').text('error');
        $('#stat-elements').text('error');
        $('#stat-bond-orders').text('error');
    }

    function formatCounts(counts) {
        const keys = Object.keys(counts || {}).sort();
        if (!keys.length) return '-';
        return keys.map(k => `${k}: ${counts[k]}`).join(' | ');
    }

    function formatBondOrders(distribution) {
        const keys = Object.keys(distribution || {}).sort((a, b) => Number(a) - Number(b));
        if (!keys.length) return '-';
        return keys.map(k => `Order ${k}: ${distribution[k]}`).join(' | ');
    }

    function bindDragRotate() {
        const container = $('#svg-container');

        container.on('mousedown', function(e) {
            if (!$('#molecule-select').val()) return;
            state.drag.active = true;
            state.drag.moved = false;
            state.drag.startX = e.clientX;
            state.drag.startY = e.clientY;
            state.drag.lastX = e.clientX;
            state.drag.lastY = e.clientY;
        });

        $(document).on('mouseup', function() {
            if (!state.drag.active) return;
            state.drag.active = false;
            container.removeClass('dragging');
        });

        container.on('mousemove', function(e) {
            if (!state.drag.active) return;

            const totalDx = e.clientX - state.drag.startX;
            const totalDy = e.clientY - state.drag.startY;
            if (!state.drag.moved && Math.hypot(totalDx, totalDy) > 4) {
                state.drag.moved = true;
                container.addClass('dragging');
            }
            if (!state.drag.moved) return;

            const dx = e.clientX - state.drag.lastX;
            const dy = e.clientY - state.drag.lastY;
            state.drag.lastX = e.clientX;
            state.drag.lastY = e.clientY;

            state.rotation.y = (state.rotation.y + dx * 1.0) % 360;
            state.rotation.x = (state.rotation.x + dy * 1.0) % 360;
            scheduleDisplay();
        });

        container.on('mouseleave', function() {
            if (!state.drag.active) return;
            state.drag.active = false;
            container.removeClass('dragging');
        });
    }

    function bindSvgInteractions() {
        const svg = $('#svg-container svg');
        if (!svg.length) return;

        const atoms = svg.find('.atom');
        const bonds = svg.find('.bond');
        const atomElementByIndex = {};

        atoms.each(function() {
            const atom = $(this);
            atomElementByIndex[Number(atom.data('atom-index'))] = atom.data('element');
        });

        atoms.on('mouseenter', function(e) {
            const atom = $(this);
            showTooltip(e, `Atom ${Number(atom.data('atom-index')) + 1}: ${atom.data('element')}`);
            atom.addClass('hovered');
        }).on('mousemove', moveTooltip)
          .on('mouseleave', function() {
              hideTooltip();
              $(this).removeClass('hovered');
          }).on('click', function(e) {
              e.stopPropagation();
              if (state.drag.moved) return;
              const atomIndex = Number($(this).data('atom-index'));
              state.selectedAtomIndex = (state.selectedAtomIndex === atomIndex) ? null : atomIndex;
              applySelection();
          });

        bonds.on('mouseenter', function(e) {
            const bond = $(this);
            const a1 = Number(bond.data('a1'));
            const a2 = Number(bond.data('a2'));
            const e1 = atomElementByIndex[a1] || '?';
            const e2 = atomElementByIndex[a2] || '?';
            const order = bond.data('epairs');
            showTooltip(e, `Bond ${Number(bond.data('bond-index')) + 1}: ${e1}${a1 + 1} - ${e2}${a2 + 1} (Order ${order})`);
            bond.addClass('hovered');
        }).on('mousemove', moveTooltip)
          .on('mouseleave', function() {
              hideTooltip();
              $(this).removeClass('hovered');
          });

        svg.on('click', function(e) {
            if (e.target === this) {
                state.selectedAtomIndex = null;
                applySelection();
            }
        });
    }

    function applySelection() {
        const svg = $('#svg-container svg');
        const atoms = svg.find('.atom');
        const bonds = svg.find('.bond');

        clearHighlights();
        if (state.selectedAtomIndex === null) {
            setSelectionInfo('Click an atom to inspect its neighborhood.');
            return;
        }

        atoms.addClass('dimmed');
        bonds.addClass('dimmed');

        const selected = atoms.filter(`[data-atom-index="${state.selectedAtomIndex}"]`);
        if (!selected.length) {
            state.selectedAtomIndex = null;
            clearHighlights();
            setSelectionInfo('Click an atom to inspect its neighborhood.');
            return;
        }

        selected.removeClass('dimmed').addClass('selected');
        const selectedElement = selected.data('element');
        const neighborIndices = [];

        bonds.each(function() {
            const bond = $(this);
            const a1 = Number(bond.data('a1'));
            const a2 = Number(bond.data('a2'));
            if (a1 === state.selectedAtomIndex || a2 === state.selectedAtomIndex) {
                bond.removeClass('dimmed').addClass('connected');
                neighborIndices.push(a1 === state.selectedAtomIndex ? a2 : a1);
            }
        });

        neighborIndices.forEach(idx => {
            atoms.filter(`[data-atom-index="${idx}"]`).removeClass('dimmed').addClass('neighbor');
        });

        setSelectionInfo(
            `Atom ${state.selectedAtomIndex + 1} (${selectedElement}) | Neighbors: ${neighborIndices.length}`
        );
    }

    function clearHighlights() {
        $('#svg-container .atom').removeClass('selected neighbor hovered dimmed');
        $('#svg-container .bond').removeClass('connected hovered dimmed');
    }

    function setSelectionInfo(text) {
        $('#selection-info').text(text);
    }

    function showTooltip(event, text) {
        $('#mol-tooltip').text(text).removeClass('hidden');
        moveTooltip(event);
    }

    function moveTooltip(event) {
        $('#mol-tooltip').css({
            left: `${event.pageX + 14}px`,
            top: `${event.pageY + 14}px`
        });
    }

    function hideTooltip() {
        $('#mol-tooltip').addClass('hidden');
    }
});
