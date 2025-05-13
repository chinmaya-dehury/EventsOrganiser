import { EventDetails, EventSettings, EventTag } from "@/interfaces/global_interfaces.ts";

export type EventFetchDirection = "forward" | "backward";

export interface EventsGetResponse {
    items: EventDetails[],
    total: number,
    page: number,
    size: number,
    pages: number,
}

export interface CalendarLinkGetResponse {
    link: string
}

export function getTags(): Promise<EventTag[]> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/tags`, {
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then(resp => {
        return resp as EventTag[]
    })
}

export function getEvents(
    direction: EventFetchDirection,
    from_time: string, // ISO8601 date
    page: number = 1,
): Promise<EventsGetResponse> {
    var url = new URL(`${import.meta.env.VITE__DOMAIN_URL}/api/events/all`);
    url.searchParams.append("direction", direction);
    url.searchParams.append("from_time", from_time);
    url.searchParams.append("page", page.toString());

    return fetch(url, {
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then(resp => {
        return resp as EventsGetResponse;
    })
}

export function updateEvent(event: EventDetails) {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/event/${event.id}`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ ...event }),
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        return;
    })
}

export function deleteEvent(event: EventDetails) {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/event/${event.id}`, {
        method: "DELETE",
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        return;
    })
}

export function getCalendarLink(): Promise<string> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/calendar/link`, {
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then((resp) => {
        return (resp as CalendarLinkGetResponse).link;
    })
}

export function changeCalendarLink(): Promise<string> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/calendar/link`, {
        method: "POST",
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then((resp) => {
        return (resp as CalendarLinkGetResponse).link;
    })
}

export function deleteCalendarLink() {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/calendar/link`, {
        method: "DELETE",
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        return;
    });
}

export function getEventSettings(): Promise<EventSettings> {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/settings`, {
        method: "GET",
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then((resp) => {
        if(!resp.ok)
            throw resp;
        
        return resp.json();
    }).then(resp => {
        return resp as EventSettings;
    })
}

export function updateEventSettings(newSettings: EventSettings) {
    return fetch(`${import.meta.env.VITE__DOMAIN_URL}/api/events/settings`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(newSettings),
        credentials: import.meta.env.VITE__CREDENTIALS_SETTING
    }).then(resp => {
        if(!resp.ok)
            throw resp;
        return;
    })
}