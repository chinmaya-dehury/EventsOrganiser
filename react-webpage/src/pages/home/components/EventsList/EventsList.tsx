import { ActiveTab, EventDetails } from "@/interfaces/global_interfaces";
import { EventAccordion } from "../EventAccordion";
import { ComponentProps } from "react";

interface Dictionary<T> {
    [Key: string]: T
};

const groupEventsByYearAndMonth = (events: EventDetails[]): Dictionary<EventDetails[]> =>  {
    let groupedByYM = events.reduce((currentGroups: Dictionary<EventDetails[]>, event: EventDetails) => {
        if(!event.start_date && !event.end_date) {
            console.error(`groupEventsByYearAndMonth: Error with event ${event.id}, does not have any dates to work with...`);
            return currentGroups;
        }

        let dateToGroupWith: string = (event.start_date || event.end_date)!;
        let key = new Date(dateToGroupWith).toLocaleString("en-US", { month: "long", year: "numeric" }) // { timeZone: 'UTC' }? all event dates are stored as UTC timestamps in database
        if (!currentGroups.hasOwnProperty(key))
            currentGroups[key] = []

        currentGroups[key].push(event);
        return currentGroups;
    }, {});

    return groupedByYM;
}

const sortEvents = (events: EventDetails[], tab: ActiveTab): EventDetails[] => {
    return [ ...events ].sort((a, b) => {
        let aDate: Date = new Date((a.start_date || a.end_date)!);
        let bDate: Date = new Date((b.start_date || b.end_date)!);

        if(tab == ActiveTab.UPCOMING)
            return aDate.valueOf() - bDate.valueOf();
        else
        return bDate.valueOf() - aDate.valueOf();
    })
}

interface EventsListProps extends ComponentProps<"div"> {
    events: EventDetails[],
    tab: ActiveTab
};

function EventsList({ events, tab, ...props }: EventsListProps) {
    events = sortEvents(events, tab);
    var groupedEvents = groupEventsByYearAndMonth(events);
    var headerAndEvents: JSX.Element[] = Object.entries(groupedEvents).map(([header, events]) => {
        return (
            <>
                <h1>{header}</h1>
                {events.map(event => <EventAccordion key={event.id} event={event}/>)}
            </>
        );
    });

    if(headerAndEvents.length === 0)
        headerAndEvents[0] = (
            <div style={{textAlign: "center"}}>No events found</div>
        );

    return (
        <div {...props}>
            {headerAndEvents}
        </div>
    )
}

export default EventsList;