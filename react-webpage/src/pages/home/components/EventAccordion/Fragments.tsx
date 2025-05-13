import { IoCalendarClearOutline  } from "react-icons/io5";
import DatePicker from "react-datepicker";

import { InputWithIcon } from '@/components';
import { EventType, EditableEventDetails } from "./interfaces";
import { EventDetails } from "@/interfaces/global_interfaces";
import * as helpers from "./eventAccordionHelpers";

interface EventDetailProps {
    header: string,
    text: JSX.Element | string | null
}

export function EventDetailColumn({ header, text }: EventDetailProps) {
    let displayedText: JSX.Element | string = text ? text : "N/A";

    return (
        <div className="event-detailed-info">
            <h3>{header}</h3>
            <span>{displayedText}</span>
        </div>
    )
}

interface DateFragmentProps {
    date?: string | null,
    threeDots?: boolean
}

export function DateText({ threeDots, date }: DateFragmentProps) {
    if(!date) 
        return null;
    
    let dayNr: string = new Date(date).toLocaleString("default", { day: "2-digit" });
    let monthShort: string = new Date(date).toLocaleString("default", { month: "short" }).toUpperCase();
    
    if(threeDots) {
        dayNr = "...";
        monthShort = " ";
    }
        
    return (
        <div className="event-date">
            <h2>{dayNr}</h2>
            <span>{monthShort}</span>
        </div>
    );
}

interface ElementProps {
    event: EventDetails,
};

interface EditableElementProps {
    event: EditableEventDetails,
    setKeyOfEditableEvent: <K extends keyof EditableEventDetails>(key: K, value: EditableEventDetails[K]) => void
}

export function HeaderDateDisplay({ event }: ElementProps) {
    if(!event.start_date && !event.end_date) {
        console.error("Invalid event start & end date for: ", event);
        return null;
    }

    let startDateElement: JSX.Element | null = null; //event.start_date ? <DateFragment date={event.start_date} /> : null;
    let endDateElement: JSX.Element | null = null; //event.end_date ? <DateFragment date={event.end_date} /> : null;

    switch(helpers.getEventType(event)) {
        case EventType.DEADLINE: {
            startDateElement = <DateText threeDots={true} date={"-"} />
            endDateElement = <DateText date={event.end_date} />;
            break;
        }
        case EventType.SINGLEDAY: {
            startDateElement = <DateText date={event.start_date} />
            break;
        }
        case EventType.MULTIDAY: {
            startDateElement = <DateText date={event.start_date} />
            endDateElement = <DateText date={event.end_date} />;
        }
    }

    let lineBetweenDates = startDateElement && endDateElement ? <hr/> : null;

    return (
        <>
            {startDateElement}
            {lineBetweenDates}
            {endDateElement}
        </>
    )
}

export function EventAccordionEditableHeader({ event, setKeyOfEditableEvent }: EditableElementProps) {
    return (
        <div style={{display: "flex", flexFlow: "wrap", alignItems: "center"}}>
            <DatePicker 
                selected={event.start_date}
                onChange={newDate => setKeyOfEditableEvent("start_date", newDate)}

				formatWeekDay={name => name.substring(0, 1)} 
                placeholderText="DD/MM/YYYY"
				customInput={
					<InputWithIcon className="search-bar" type="text">
						<IoCalendarClearOutline className="icon" />
					</InputWithIcon>
				}
			/>
            <h3 style={{margin: "0.5rem"}}>to</h3>
            <DatePicker 
                required

                selected={event.end_date}
                onChange={newDate => setKeyOfEditableEvent("end_date", newDate)}

				formatWeekDay={name => name.substring(0, 1)} 
                placeholderText="DD/MM/YYYY"
				customInput={
					<InputWithIcon className="search-bar" type="text">
						<IoCalendarClearOutline className="icon" />
					</InputWithIcon>
				}
			/>

            <input type="text" placeholder="Event name" value={event.event_name} onChange={(e) => setKeyOfEditableEvent("event_name", e.target.value)} />
        </div>
    );
}

export function EventAccordionHeader({ event }: ElementProps) {
    return (
        <>
            <div className="event-date-container">
                <HeaderDateDisplay event={event} />
            </div>

            <div className="event-name">
                <h2>{event.event_name}</h2>
            </div>
        </>
    )
}