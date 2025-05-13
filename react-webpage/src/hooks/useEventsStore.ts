import { EventDetails, EventTag } from "@/interfaces/global_interfaces";
import { create } from "zustand";

export type EventChangerFunc = (events: EventDetails[]) => void;

export interface EventsState {
    events: EventDetails[],
    tags: EventTag[],
    calendarLink?: string,
    calendarLinkFetched: boolean,

    addOrUpdate: EventChangerFunc,
    deleteEvents: EventChangerFunc,
    setTags: (tags: EventTag[]) => void,
    setCalendarLink: (link?: string) => void
}

function addOrUpdateEvents(prevEvents: EventDetails[], newEvents: EventDetails[]) {
    let idToEvent = new Map(prevEvents.map(event => [event.id, event]));

    newEvents.forEach(event => idToEvent.set(event.id, event));

    return [ ...idToEvent.values() ];
}

function deleteEvents(prevEvents: EventDetails[], removeEvents: EventDetails[]) {
    let removableEventIds: Set<number> = new Set(removeEvents.map(event => event.id));

    return prevEvents.filter(event => !removableEventIds.has(event.id));
}

const useEventsStore = create<EventsState>((set) => ({
    events: [],
    tags: [],
    calendarLink: undefined,
    calendarLinkFetched: false,

    addOrUpdate: (newEvents: EventDetails[]) => {
        set((state) => ({
            ...state,
            events: addOrUpdateEvents(state.events, newEvents)
        }));
    },
    deleteEvents: (removeEvents: EventDetails[]) => {
        set((state) => ({
            ...state,
            events: deleteEvents(state.events, removeEvents)
        }));
    },
    setTags: (newTags) => {
        set((state) => ({
            ...state,
            tags: newTags
        }));
    },
    setCalendarLink: (link?: string) => {
        set((state) => ({
            ...state,
            calendarLink: link,
            calendarLinkFetched: true
        }))
    }
}));

export default useEventsStore;