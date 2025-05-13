import { getEventSettings, updateEventSettings } from "@/apis/events";
import { getMicrosoftAccountSettings, updateMicrosoftAccountSettings } from "@/apis/microsoft";
import { Settings } from "@/interfaces/global_interfaces";

// only gets the unloaded settings
export function loadSettings(settings: Partial<Settings>) {
    let promises: Promise<Partial<Settings>>[] = [];

    if(!settings.accountSettings) {
        let prm = getMicrosoftAccountSettings()
        .then((accountSettings) => {
            return {
                accountSettings: accountSettings
            }
        });
        promises.push(prm);
    }

    if(!settings.eventSettings) {
        let prm = getEventSettings()
        .then((eventSettings) => {
            return {
                eventSettings: eventSettings
            }
        });
        promises.push(prm);
    }

    return Promise.allSettled(promises);
}

export function areSettingsFullyLoaded(settings: Partial<Settings>) {
    type AllSettingKeys = Record<keyof Settings, undefined>;
    const allSettingObjKeys: AllSettingKeys = {
        accountSettings: undefined,
        eventSettings: undefined
    }

    for(const key in allSettingObjKeys) {
        if(settings[key as keyof Settings] === undefined)
            return false;
    }
    return true;
}

export function updateSettings(newSettings: Settings) {
    let promises: Promise<void>[] = [];
    promises.push(
        updateMicrosoftAccountSettings(newSettings.accountSettings)
    );

    promises.push(
        updateEventSettings(newSettings.eventSettings)
    );

    return Promise.allSettled(promises);
}