import { AccountSettings } from "@/interfaces/global_interfaces";

export interface EmailsFetchResponse {
    count: number
}

export function fetchNewEmails(): Promise<EmailsFetchResponse> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/microsoft/emails/fetch_new`, {
        method: "POST",
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then(resp => {
        return resp as EmailsFetchResponse;
    })
}

export function getMicrosoftAccountSettings(): Promise<AccountSettings> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/microsoft/settings`, {
        method: "GET",
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then(resp => {
        return resp as AccountSettings;
    })
}

export function updateMicrosoftAccountSettings(newSettings: AccountSettings) {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/microsoft/settings`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(newSettings),
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        return;
    })
}