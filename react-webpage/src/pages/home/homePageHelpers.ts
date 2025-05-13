import { EventDetails, ActiveTab } from "@/interfaces/global_interfaces";
import { SearchOptions } from "./components";

export const filterEventsForTab = (events: EventDetails[], showEvtType: ActiveTab) => {
    let filtered: EventDetails[] = [];
    const currDate = new Date();

    switch(showEvtType) {
        case ActiveTab.PAST: {
            filtered = events.filter((event) => new Date(event.end_date) < currDate);
            break;
        }
        case ActiveTab.ONGOING: {
            filtered = events.filter((event) => currDate <= new Date(event.end_date) && (!event.start_date || new Date(event.start_date) <= currDate));
            break;
        }
        case ActiveTab.UPCOMING: {
            filtered = events.filter((event) => (event.start_date && currDate < new Date(event.start_date)) || (event.end_date && currDate < new Date(event.end_date)));
            break;
        }
    }

    return filtered;
};

export const applySearchQuery = (events: EventDetails[], searchOptions: SearchOptions): EventDetails[] => {
    if(searchOptions.eventName && searchOptions.eventName?.length > 1)
        events = events.filter((event) => event.event_name.toLowerCase().includes(searchOptions.eventName!.toLowerCase()) );
    
    if(searchOptions.startDate)
        events = events.filter((event) => {
            if(event.start_date)
                return new Date(event.start_date) >= searchOptions.startDate!;
            else
                return new Date(event.end_date) >= searchOptions.startDate!;
        });

    if(searchOptions.endDate) {
        searchOptions.endDate.setHours(23, 59, 59)
        events = events.filter((event) => new Date(event.end_date) <= searchOptions.endDate!);
    }

    if(searchOptions.tags && searchOptions.tags.length > 0)
        events = events.filter((event) => {
            let eventTagIds: Set<number> = new Set(event.tags.map(tag => tag.id));

            return searchOptions.tags!.map(tag => tag.id).every(tagId => eventTagIds.has(tagId))
        });

    return events;
}