import { IoIosSearch } from "react-icons/io";
import { IoCalendarClearOutline } from "react-icons/io5";
import DatePicker from "react-datepicker";

import { InputWithIcon, StyledSelect } from "@/components";
import { EventTag } from "@/interfaces/global_interfaces";
import { useEffect, useState } from "react";
import { useEventsStore } from "@/hooks";

export interface SearchOptions {
    eventName?: string,
    startDate?: Date | null,
    endDate?: Date | null,
    tags?: EventTag[],
}

interface SearchBarProps {
    searchCallback: (opts: SearchOptions) => void;
}

const pStyle = {margin: "0rem", marginTop: "0.5rem", marginLeft: "0.35rem"};

function SearchBar({ searchCallback }: SearchBarProps) {
    const { tags } = useEventsStore();
    const [searchOptions, setSearchOptions] = useState<SearchOptions>({ });

    const updateSearchOptKey = <K extends keyof SearchOptions>(key: K, value: SearchOptions[K]) => {
        setSearchOptions(prev => ({
                ...prev,
                [key]: value
            })
        );
    }

    useEffect(() => {
        searchCallback(searchOptions);
    }, [searchOptions]);
    
    return (
        <aside style={{display: "flex", flexDirection: "column"}}>
            <InputWithIcon type="text" placeholder="Event name..." value={searchOptions.eventName} onChange={(e) => updateSearchOptKey("eventName", e.target.value)}>
                <IoIosSearch className="icon" />
            </InputWithIcon>

            <p style={pStyle}><b>Start date</b></p>
            <DatePicker 
                selected={searchOptions.startDate}
                onChange={d => updateSearchOptKey("startDate", d)}

                formatWeekDay={name => name.substring(0, 1)} 
                placeholderText="DD/MM/YYYY"
                customInput={
                    <InputWithIcon className="search-bar" type="text">
                        <IoCalendarClearOutline className="icon" />
                    </InputWithIcon>
                }
            />

            <p style={pStyle}><b>End date</b></p>
            <DatePicker 
                selected={searchOptions.endDate}
                onChange={d => updateSearchOptKey("endDate", d)}

                formatWeekDay={name => name.substring(0, 1)} 
                placeholderText="DD/MM/YYYY"
                customInput={
                    <InputWithIcon className="search-bar" type="text">
                        <IoCalendarClearOutline className="icon" />
                    </InputWithIcon>
                }
            />

            <p style={pStyle}><b>Event categories</b></p>
            <StyledSelect
                options={tags}
                isMulti
                isSearchable
                getOptionLabel={tag => tag.name}
                getOptionValue={tag => tag.id.toString()}
                onChange={(newValues) => updateSearchOptKey("tags", newValues as EventTag[])}
            /> { /* TODO: Style */ }
        </aside>
    );
}

export default SearchBar;