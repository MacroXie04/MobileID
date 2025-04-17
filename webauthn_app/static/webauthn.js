const {startRegistration, startAuthentication} = SimpleWebAuthnBrowser;

function getCSRFToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

window.registerPasskey = async function () {
    try {
        const response = await fetch('/passkey/reg/options', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const options = await response.json();

        const registrationResponse = await startRegistration(options);

        const completeResponse = await fetch('/passkey/reg/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(registrationResponse),
        });

        const result = await completeResponse.json();
        if (result.status === 'ok') {
            alert('Passkey registration successful! You can now log in with your passkey.');
        } else {
            alert('Passkey registration field: ' + JSON.stringify(result));
        }
    } catch (error) {
        console.error('Passkey registration field: ', error);
        alert('Passkey registration field: ' + error.message);
    }
}

window.loginWithPasskey = async function () {
    try {
        const response = await fetch('/passkey/auth/options', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const options = await response.json();

        const authenticationResponse = await startAuthentication(options);

        const completeResponse = await fetch('/passkey/auth/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(authenticationResponse),
        });

        const result = await completeResponse.json();
        if (result.status === 'ok') {
            window.location.href = '/';
        } else {
            alert('Passkey login field: ' + JSON.stringify(result));
        }
    } catch (error) {
        console.error('Passkey login field: ', error);
        alert('Passkey login field: ' + error.message);
    }
}