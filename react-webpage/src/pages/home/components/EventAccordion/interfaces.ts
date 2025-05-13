import { EventTag } from "@/interfaces/global_interfaces";

export enum EventType {
    INVALID,
    DEADLINE,
    SINGLEDAY,
    MULTIDAY
};


export interface EditableEventDetails {
    event_name: string,
    address: string,
    start_date: Date | null,
    start_time: string,
    end_date: Date | null,
    end_time: string,
    tags: EventTag[]
};
