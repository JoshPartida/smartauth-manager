async function downloadKey(actionButton, rowId, referenceObject){
    $('.content.segment>.dimmer').dimmer('show');
    const url = `oidc/proveedor/rsa/${referenceObject.pk}/descargar/`;
    const response = await fetch(url);
    if (response.status == 200) {
        const disposition = response.headers.get('content-disposition');
        let filename = 'rsa_key.pem';
        if (disposition && disposition.includes('filename=')) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) { 
                filename = matches[1].replace(/['"]/g, '');
            }
        }
        const blob = await response.blob();
        const download_link = document.createElement('a');
        download_link.href = URL.createObjectURL(blob);
        download_link.download = filename;
        document.body.appendChild(download_link);
        download_link.click();
        document.body.removeChild(download_link);
        URL.revokeObjectURL(download_link.href);
    }
    $('.content.segment>.dimmer').dimmer('hide')

    // fetch(url).then(function(response) {
    //     if (response.status == 200) {
    //         const disposition = response.headers.get('content-disposition');
    //         let filename = 'rsa_key.pem';
    //         if (disposition && disposition.includes('filename=')) {
    //             const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
    //             const matches = filenameRegex.exec(disposition);
    //             if (matches != null && matches[1]) { 
    //                 filename = matches[1].replace(/['"]/g, '');
    //             }
    //         }
    //         response.blob().then(function(blob) {
    //             const download_link = document.createElement('a');
    //             download_link.href = URL.createObjectURL(blob);
    //             download_link.download = filename;
    //             document.body.appendChild(download_link);
    //             download_link.click();
    //             document.body.removeChild(download_link);
    //             URL.revokeObjectURL(download_link.href); 
    //         });
    //     }
    // }).finally(() => $('.content.segment>.dimmer').dimmer('hide'));
}

function uploadKeyCallback(event) {
    const fileInput = event.target
    const form = fileInput.closest('form');
    const dropZone = fileInput.parentElement.querySelector('.dragdrop.segment');
    form.classList.add("loading");
    const actions = document.querySelectorAll('.modal .actions > .ui.button');
    actions.forEach((action) => {
        action.classList.add('disabled');
    });
    const files = fileInput.files;
    for (const file of files) {
        if (file.type != '') {
            dropZone.classList.remove('tertiary');
            $.toast({class: 'warning', title: 'Archivo no válido', message: 'El tipo de archivo especificado no es válido.'});
            fileInput.value = null;
            form.classList.remove("loading");
            actions.forEach((action) => {
                action.classList.remove('disabled');
            });
        } else {
            const modalId = fileInput.closest('.ui.modal .content').id;
            closeContentModal(modalId, "Archivo cargado correctamente", "", "success");
        }
    }
}