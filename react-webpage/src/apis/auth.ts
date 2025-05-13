export function getMicrosoftLoginLink(timezone: string): Promise<string> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/auth/microsoft/`, {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ timezone }),
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then(resp => {
        return resp as string;
    })
}

export function deleteAccount(): Promise<void> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/auth/delete_account/`, {
        method: "POST",
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then(_ => {
        return;
    })
}