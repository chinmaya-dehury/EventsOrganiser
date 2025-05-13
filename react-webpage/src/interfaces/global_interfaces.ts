export interface EventDetails {
    id: number,
    event_name: string,
    start_date?: string | null,
    end_date: string,
    address: string,
    tags: EventTag[],

    email_link: string
}

export interface JWTData {
    account_id: string,
    account_type: string,
    sub: string,
    exp: number
}

export interface AccountSettings {
    auto_fetch_emails: boolean,
    timezone: string // IANA timezone
}

export interface EventSettings {
    categories: EventTag[],
}

export interface Settings {
    accountSettings: AccountSettings,
    eventSettings: EventSettings
}

export interface EventTag {
    id: number,
    name: string
}

export enum ActiveTab {
    PAST = "past",
    ONGOING = "ongoing",
    UPCOMING = "upcoming",
}
