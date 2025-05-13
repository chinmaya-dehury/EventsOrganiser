import { ComponentProps } from "react";

export interface SettingRowProps extends ComponentProps<"div"> {
    settingName: string,
    description: string
}

export default function SettingRow({ settingName, description, children }: SettingRowProps) {
    return (
        <>
            <div className="setting-row">
                <div className="col1">
                    <h3 className="setting-type">{settingName}</h3>
                    <span className="setting-description">{description}</span>
                </div>
                <div className="col2">
                    {children}
                </div>
            </div>
        </>
    )
}