import { EventDetails } from "@/interfaces/global_interfaces";
import { EventType, EditableEventDetails } from "./interfaces";

export const formatTags = (event: EventDetails) => {
    let tagNames: string[] = event.tags.map(tag => tag.name);
    return tagNames.join(", ");
}

export const getEventType = (event: EventDetails): EventType => {
    if(!event.start_date && !event.end_date)
        return EventType.INVALID;

    if(!event.start_date && event.end_date) 
        return EventType.DEADLINE;

    // extra check to see if start and end date are within the same day
    let startDateObj: Date = new Date(event.start_date!);
    let endDateObj: Date = new Date(event.end_date!);
    if(startDateObj.getDate() === endDateObj.getDate())
        return EventType.SINGLEDAY;
    else
        return EventType.MULTIDAY;
}

export const createEditableEventObject = (event: EventDetails): EditableEventDetails => {
    return {
        event_name: event.event_name,
        address: event.address,
        start_date: event.start_date ? new Date(new Date(event.start_date).toDateString()) : null,
        start_time: format8601TimestampToTime(event.start_date),
        end_date: new Date(new Date(event.end_date).toDateString()),
        end_time: format8601TimestampToTime(event.end_date),
        tags: event.tags
    };
}

export const editableEventToEventDetails = (origEvent: EventDetails, event: EditableEventDetails): EventDetails => {
    event.start_date?.setHours(Number(event.start_time?.split(":")[0]), Number(event.start_time?.split(":")[1]));
    event.end_date?.setHours(Number(event.end_time?.split(":")[0]), Number(event.end_time?.split(":")[1]));

    return {
        id: origEvent.id,
        event_name: event.event_name,
        start_date: event.start_date ? event.start_date.toISOString() : null,
        end_date: event.end_date!.toISOString(),
        address: event.address,
        tags: event.tags,
        email_link: origEvent.email_link
    };
}

export const format8601TimestampToTime = (utcDateTime?: string | null): string => {
    if(!utcDateTime)
        return "";

    return new Date(utcDateTime).toLocaleString("default", { hour: "2-digit", minute: "2-digit" })
}

export const exactlyOneNull = (a: any, b: any): boolean => {
    return (!a) !== (!b);
}

export const validateEditableEvent = (event: EditableEventDetails): string[] => {
    let errors: string[] = [];
    if(!event.end_date && !event.end_time)
        errors.push("The event must have an end date");

    if(exactlyOneNull(event.start_date, event.start_time))
        errors.push("Both start time and start date must be chosen");

    if(exactlyOneNull(event.end_date, event.end_time))
        errors.push("Both end time and end date must be chosen");

    if(event.end_date && event.start_date && event.end_date < event.start_date)
        errors.push("End date must be after start date"); 

    // direct string comparision works since the times are in 00:00 24h format
    if(event.end_time && event.start_time && event.end_time < event.start_time)
        errors.push("End date must be after start date"); 

    return errors;
}