$(document).ready(() => {
    // Initialize Select2 on both dropdowns with full width
    $('.select2').select2({
        width: '100%' // Explicitly set width to 100%
    });

    const tingkatPendidikanSelect = $('#tingkat_pendidikan');
    const programStudiSelect = $('#program_studi');
    const getKodeBtn = $('#get_kode_btn');
    const kodeContainer = $('#kode-container');
    const cepatKodeInput = $('#kode_ref_pend');
    const copyBtn = $('#copy_btn');
    const fetchForm = $('#fetch-form');
    const logOutput = $('#log-output');

    // Fetch and populate Tingkat Pendidikan options
    fetch('/api/tingkat_pendidikan')
        .then(response => response.json())
        .then(data => {
            data.forEach(({ id, nama }) => {
                const option = new Option(nama, id);
                tingkatPendidikanSelect.append(option).trigger('change');
            });
        })
        .catch(err => console.error('Error fetching tingkat_pendidikan:', err));

    // Event listener for Tingkat Pendidikan selection change
    tingkatPendidikanSelect.on('change', function() {
        const selectedTingkat = $(this).val();
        programStudiSelect.empty().trigger('change');
        kodeContainer.addClass('hidden');

        if (selectedTingkat) {
            // Fetch and populate Program Studi based on selected Tingkat Pendidikan
            fetch(`/api/program_studi?tingkat_pendidikan_id=${encodeURIComponent(selectedTingkat)}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(program => {
                        const option = new Option(program, program);
                        programStudiSelect.append(option).trigger('change');
                    });

                    // After populating Program Studi, listen for changes
                    programStudiSelect.on('change', function() {
                        const selectedProgram = $(this).val();
                        if (selectedProgram) {
                            fetchCepatKode(selectedTingkat, selectedProgram);
                        }
                    });
                })
                .catch(err => console.error('Error fetching program_studi:', err));
        }
    });

    // Function to fetch cepat_kode based on selections
    function fetchCepatKode(tingkatPendidikan, programStudi) {
        fetch(`/api/get_cepat_kode?tingkat_pendidikan_id=${encodeURIComponent(tingkatPendidikan)}&program_studi=${encodeURIComponent(programStudi)}`)
            .then(response => response.json())
            .then(data => {
                if (data.cepat_kode) {
                    cepatKodeInput.val(data.cepat_kode);
                    kodeContainer.removeClass('hidden');
                } else if (data.error) {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch(err => console.error('Error fetching cepat_kode:', err));
    }

    // Event listener for Get Kode button
    getKodeBtn.on('click', () => {
        const selectedTingkat = tingkatPendidikanSelect.val();
        const selectedProgram = programStudiSelect.val();

        if (!selectedTingkat || !selectedProgram) {
            alert('Please select both Tingkat Pendidikan and Program Studi.');
            return;
        }

        fetchCepatKode(selectedTingkat, selectedProgram);
    });

    // Modern copy functionality with feedback
    copyBtn.on('click', async () => {
        try {
            await navigator.clipboard.writeText(cepatKodeInput.val());
            copyBtn.text('Copied!');
            setTimeout(() => copyBtn.text('Copy'), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            alert('Failed to copy the text to clipboard.');
        }
    });

    // Fetch records form submission
    fetchForm.on('submit', async function (e) {
        e.preventDefault(); // Prevent default form submission
        const kodeRefPend = $('#kode_ref_pend').val();

        if (!kodeRefPend) {
            alert('Please enter a Kode Ref Pend.');
            return;
        }

        try {
            const response = await fetch(`/fetch-records?kode_ref_pend=${encodeURIComponent(kodeRefPend)}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${kodeRefPend}_records.csv`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            // After saving the CSV, reload the page after a short delay
            setTimeout(() => {
                location.reload();
            }, 1000);
        } catch (err) {
            console.error('Error fetching records:', err);
        }
    });

    // WebSocket for log output
    const socket = io();
    socket.on('log', ({ message }) => {
        const logElement = document.createElement('div');
        logElement.textContent = message;
        logOutput.append(logElement);
        logOutput.scrollTop(logOutput[0].scrollHeight); // Auto-scroll to bottom
    });
});
