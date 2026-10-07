function toggleUserStatus(actionButton, rowId, referenceObject) {
    const csrf_token = actionButton.dataset.csrf;
    let actionStr = "habilitar"
    let action = true;
    if (referenceObject.is_active == 'True') {
        actionStr = 'des' + actionStr;
        action = false;
    }
    actionStr = actionStr.charAt(0).toUpperCase() + actionStr.slice(1);
    $.modal('confirm', {
        title: `${actionStr} usuario "${referenceObject.username}"`,
        content: `¿Estás seguro que deseas ${actionStr.toLowerCase()} al usuario "${referenceObject.username}"?`,
        handler: function(choice) {
            if (!choice) return true;
            $('.content.segment>.dimmer').dimmer('show');
            const url = `auth/usuarios/cambiarEstatus/`;
            const data = {username: referenceObject.username, action: action};
            fetch(url, {
                method: 'POST', 
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf_token}, 
                body: JSON.stringify(data)
            }).then((response) => { 
                response.json().then((data) => {
                    const toastOptions = {}
                    toastOptions.class = data.result;
                    toastOptions['showProgress'] = 'bottom';
                    toastOptions['className'] = {
                        toast: 'ui message'
                    };
                    toastOptions.context = '.ui.main.segments';
                    if (data.message) {
                        if (data.result == 'success') {
                            toastOptions.title = data.message;
                        } else if (data.result == 'warning') {
                            toastOptions.title = 'Problemas con la solicitud';
                            toastOptions.message = data.message;
                        } else if (data.result == 'error') {
                            toastOptions.title = 'Ocurrió un error al procesar la solicitud';
                            toastOptions.message = data.message;
                        }
                    }
                    $.toast(toastOptions);
                    refreshContent('auth/usuarios/');
                });
            }).catch((error) => {
                console.log(error);
                const toastOptions = {}
                toastOptions.class = "error";
                toastOptions['showProgress'] = 'bottom';
                toastOptions['className'] = {
                    toast: 'ui message'
                };
                toastOptions.context = '.ui.main.segments';
                toastOptions.title = 'Ocurrió un error al procesar la solicitud';
                toastOptions.message = 'Intente de nuevo más tarde';
                $.toast(toastOptions);
            })
            .finally(() => {
                $('.content.segment>.dimmer').dimmer('hide')
            });
        }
    })
}