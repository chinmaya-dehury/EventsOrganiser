import { Settings } from "@/interfaces/global_interfaces";
import { create } from "zustand";

interface AccountData {
    authenticated: boolean,
    settings: Partial<Settings>,

    setAuthenticated: (val: boolean) => void;
    updateSettings: (newSettings: Partial<Settings>) => void;
}

const useAccountDataStore = create<AccountData>((set) => ({
    authenticated: false,
    settings: {},
    
    setAuthenticated: (val) => {
        set((state) => ({
            ...state,
            authenticated: val,
        }));
    },
    updateSettings: (newSettings) => {
        set((state) => ({
            ...state,
            settings: Object.assign(state.settings, newSettings),
        }));
    }
}));

export default useAccountDataStore;