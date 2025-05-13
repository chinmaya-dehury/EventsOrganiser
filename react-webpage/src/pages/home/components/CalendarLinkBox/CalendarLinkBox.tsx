import { useState } from "react";
import { MdContentCopy } from "react-icons/md";
import { TbRefresh } from "react-icons/tb";
import { FaTrash } from "react-icons/fa";
import { AiOutlineInfoCircle } from "react-icons/ai";
import { Tooltip } from 'react-tooltip';
import { toast } from "react-toastify";
import { SpinnerCircular } from 'spinners-react';

import { changeCalendarLink, deleteCalendarLink, getCalendarLink } from "@/apis/events";
import { InputWithIcon } from "@/components";
import { useEventsStore } from "@/hooks";

import "./linkbox.css";

export default function CalendarLinkBox() {
    const { calendarLink, calendarLinkFetched, setCalendarLink } = useEventsStore();
    const [linkRequestActive, setLinkRequestActive] = useState<boolean>(false);

    const fetchLink = (type: "get" | "update") => {
        setLinkRequestActive(true);

        let promise: Promise<string> = type === "get" ? getCalendarLink() : changeCalendarLink();

        promise.then((link) => {
            // link will be undefined if 404
            setCalendarLink(link);
        }).catch(e => {
            if(e.status === 404) {
                setCalendarLink(undefined);
            } else {
                console.error("Calendar link fetch error", e);
                toast.error(`Failed to ${type} calendar link`)
            }
        }).finally(() => {
            setLinkRequestActive(false);
        })
    }

    const deleteLink = () => {
        setLinkRequestActive(true);

        deleteCalendarLink().then(() => {
            toast.success("Calendar link deleted!");
            setCalendarLink(undefined);
        }).catch(e => {
            console.error("Error deleting calendar link", e);
            toast.error("Could not delete calendar link.");
        }).finally(() => {
            setLinkRequestActive(false);
        })
    }

    let calendarLinkActions: JSX.Element = <></>;
    if(calendarLinkFetched) {
        const linkDisplayValue = !calendarLink ? "No link found" : calendarLink;

        calendarLinkActions = (
            <>
                <div style={{width: "60%"}}>
                    <InputWithIcon value={linkDisplayValue} readOnly style={{direction: "rtl", textOverflow: "ellipsis", textAlign: "left"}}>
                        <MdContentCopy 
                            className="icon" 
                            style={{cursor:"pointer"}}
                            onClick={() => navigator.clipboard.writeText(calendarLink || "")}
                        />
                    </InputWithIcon>
                </div>

                {linkRequestActive 
                ? 
                    <SpinnerCircular enabled color="black" size="2em"/>
                : 
                    <>
                        <TbRefresh 
                            data-tooltip-id="refreshBtn" 
                            className="icon-button"
                            style={{cursor: "pointer"}}
                            onClick={() => fetchLink("update")}
                        />
                        <Tooltip 
                            id="refreshBtn"
                            content="Create/update your current calendar link"
                        />

                        {calendarLink && <FaTrash 
                            className="icon-button"
                            style={{cursor: "pointer"}}
                            onClick={deleteLink}
                        />}
                    </>
                }
            </>
        );
    } else {
        calendarLinkActions = (
            <>
                <button
                    onClick={() => fetchLink("get")}
                    disabled={linkRequestActive}
                >
                    <SpinnerCircular 
                        size={"1.5em"}
                        enabled={linkRequestActive}
                        color="white" 
                    />
                    Get calendar link
                </button>
            </>
        );
    }

    return (
        <div style={{display: "inline-flex", alignItems: "center", justifyContent: "center"}}>
            {calendarLinkActions}

            <AiOutlineInfoCircle 
                className="icon-button"
                data-tooltip-id="calLinkInfo"
            />

            <Tooltip 
                id="calLinkInfo"
            >
                <div style={{display: "flex", flexDirection: "column"}}>
                    <span>This link can be used to export events to an online calendar</span>
                    <span>(Google calendar, Outlook calendar etc)</span>
                </div>
            </Tooltip>
        </div>
    );
}