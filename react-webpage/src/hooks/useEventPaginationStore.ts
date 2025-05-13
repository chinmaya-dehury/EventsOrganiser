import { ActiveTab } from "@/interfaces/global_interfaces";
import { create } from "zustand";

interface TabPage {
    currPage: number,
    maxPages: number,
    isBeingFetched: boolean,
}

type TabsPagination = {
    [key in ActiveTab]: TabPage
}

export type FinishedFetchingFunc = (tab: ActiveTab, newCurrPage?: number, maxPages?: number) => void;
export type StartFetchingFunc = (tab: ActiveTab) => void;

interface PaginationState extends TabsPagination {
    startFetching: StartFetchingFunc,
    finishedFetching: FinishedFetchingFunc
}

const useEventPagination = create<PaginationState>((set) => ({
    [ActiveTab.PAST]: {
        currPage: 0,
        maxPages: Number.MAX_SAFE_INTEGER,
        isBeingFetched: false,
    },
    [ActiveTab.ONGOING]: {
        currPage: 0,
        maxPages: -1,
        isBeingFetched: false,
    },
    [ActiveTab.UPCOMING]: {
        currPage: 0,
        maxPages: Number.MAX_SAFE_INTEGER,
        isBeingFetched: false,
    },
    startFetching: (tab: ActiveTab) => {
        set((state) => ({ // if this ever gets to more than 1 nested object, use a helper that zustand recommends
            ...state,
            [tab]: {
                ...state[tab],
                isBeingFetched: true
            }
        }));
    },
    finishedFetching: (tab: ActiveTab, newCurrPage?: number, maxPages?: number) => {
        set((state) => ({
            ...state,
            [tab]: {
                currPage: newCurrPage !== undefined ? newCurrPage : state[tab].currPage,
                maxPages: maxPages !== undefined ? maxPages : state[tab].maxPages,
                isBeingFetched: false
            }
        }));
    }
}));

export default useEventPagination;