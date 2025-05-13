import { useRef, useState } from "react";
import { IoIosArrowDown } from "react-icons/io";

import {EventAccordionEditableHeader, EventAccordionHeader, EventDetailColumn} from "./Fragments";
import { StyledSelect } from '@/components';
import { EventDetails, EventTag } from "@/interfaces/global_interfaces";
import { EditableEventDetails } from "./interfaces";
import * as helpers from "./eventAccordionHelpers";
import { useEventsStore } from "@/hooks";
import { SpinnerCircular } from 'spinners-react';

import "./event-accordion.scss";
import "./date.scss";
import { deleteEvent, updateEvent } from "@/apis/events";
import { toast } from "react-toastify";

interface EventAccordionProps {
	event: EventDetails
}

function EventAccordion({ event }: EventAccordionProps) {
	const [editableEvent, setEditableEvent] = useState<EditableEventDetails>(helpers.createEditableEventObject(event));
	const [isBeingEdited, setIsBeingEdited] = useState<boolean>(false);

	const [deleteReqInProgress, setDeleteReqInProgress] = useState<boolean>(false);
	const [updateReqInProgress, setUpdateReqInProgress] = useState<boolean>(false);

	const modalRef = useRef<HTMLDialogElement | null>(null);

	const { tags, addOrUpdate, deleteEvents } = useEventsStore();

	const setKeyOfEditableEvent = <K extends keyof EditableEventDetails>(key: K, value: EditableEventDetails[K]) => {
		setEditableEvent(prev => ({
				...prev,
				[key]: value
			})
		);
	}

	const saveEventChanges = () => {
		let updatedEvent = helpers.editableEventToEventDetails(event, editableEvent);
		setUpdateReqInProgress(true);

		updateEvent(updatedEvent).then(() => {
			setIsBeingEdited(false);
			addOrUpdate([updatedEvent]);
		}).catch(err => {
			console.error("Event update error", err);
			toast.error(`Failed to update event ${event.event_name}`);
		}).finally(() => {
			setUpdateReqInProgress(false);
		})
	}

	const deleteEventChanges = () => {
		setDeleteReqInProgress(true);

		deleteEvent(event).then(() => {
			deleteEvents([event]);
		}).catch(err => {
			console.error("Event deletion error", err);
			toast.error(`Failed to delete event ${event.event_name}`);
		}).finally(() => {
			modalRef.current?.close();
			setDeleteReqInProgress(false);
		})
	}

	let formErrors = helpers.validateEditableEvent(editableEvent);
	let eventButtons: JSX.Element = <></>;
	if(isBeingEdited) {
		eventButtons = (
			<>
				<button 
					disabled={formErrors.length !== 0 || updateReqInProgress}
					onClick={saveEventChanges}
				>
					<SpinnerCircular
						color="white"
						enabled={updateReqInProgress}
						size="1em"
					/>
					Save
				</button>
				<button 
					className="warning" 
					disabled={updateReqInProgress}
					onClick={() => setIsBeingEdited(false)}
				>
					Cancel
				</button>
			</>
		);
	} else {
		eventButtons = (
			<>
				<button 
					onClick={() => setIsBeingEdited(true)}
				>
					Edit
				</button>
				<button 
					className="warning" 
					onClick={() => modalRef.current?.showModal()}
				>
					Delete
				</button>
			</>
		);
	}

	let errorsList: JSX.Element[] = formErrors.map(text => <span style={{color: "red"}}>{text}</span>);
	return (
		<>
			<details className="event-accordion">
				<summary className="event-accordion-header">
					{isBeingEdited 
						? <EventAccordionEditableHeader event={editableEvent} setKeyOfEditableEvent={setKeyOfEditableEvent}/> 
						: <EventAccordionHeader event={event} /> }
		
					<div className="dd-icon-container">
						<IoIosArrowDown className="dd-icon" />
					</div>
				</summary>

				<div className="event-accordion-body">
					<div className="event-details">
						<EventDetailColumn 
							header={"Start time"} 
							text={isBeingEdited 
									? <input type="time" value={editableEvent.start_time || ""} onChange={(e) => setKeyOfEditableEvent("start_time", e.target.value)} /> 
									: helpers.format8601TimestampToTime(event.start_date)} 
						/>
						<EventDetailColumn 
							header={"End time"} 
							text={isBeingEdited 
									? <input type="time" value={editableEvent.end_time || ""} onChange={(e) => setKeyOfEditableEvent("end_time", e.target.value)} required /> 
									: helpers.format8601TimestampToTime(event.end_date)}
						/>
						<EventDetailColumn 
							header={"Venue"} 
							text={isBeingEdited 
									? <input type="text" value={editableEvent.address} onChange={(e) => setKeyOfEditableEvent("address", e.target.value)}/> 
									: event.address} 
						/>
						<EventDetailColumn 
							header={"Event categories"} 
							text={isBeingEdited
									? <StyledSelect
										options={tags}
										defaultValue={editableEvent.tags}

										menuPortalTarget={document.body}
										menuPosition={'fixed'} 

										isMulti
										isSearchable
										getOptionLabel={tag => tag.name}
										getOptionValue={tag => tag.id.toString()}
										onChange={(newValues) => setKeyOfEditableEvent("tags", newValues as EventTag[])}
									/>
									: helpers.formatTags(event)}
						/>
					</div>
					<div className="event-buttons-container">
						<div className="event-buttons">
							{eventButtons}

							<button 
								onClick={() => window.open(event.email_link, "_blank")?.focus()}
							>
								View e-mail
							</button>
						</div>
					</div>
				</div>
				{isBeingEdited 
					? <div style={{padding: "0.25rem", display: "flex", flexDirection: "column"}}>{errorsList}</div> 
					: <></> }
			</details>

			<dialog ref={modalRef}>
				<h2>Delete confirmation</h2>
				<p>Are you sure you want to delete <b>{event.event_name}</b>?</p>

				<div style={{display: "flex", justifyContent: "flex-end"}}>
					<button 
						className="plain" 
						onClick={() => modalRef.current?.close()}
						disabled={deleteReqInProgress}
					>
						Cancel
					</button>
					<button 
						className="warning" 
						onClick={deleteEventChanges}
						disabled={deleteReqInProgress}
					>
						<SpinnerCircular
							size="1em"
							color="white"
							enabled={deleteReqInProgress}
						/>
						Delete
					</button>
				</div>
			</dialog>
		</>
	)
}

export default EventAccordion;