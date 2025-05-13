
import { useState } from "react";
import { SpinnerCircular } from 'spinners-react';
import { toast } from "react-toastify"

import { getMicrosoftLoginLink } from "@/apis/auth";
import MicrosoftIcon from "@/assets/ms-symbollockup_mssymbol_19.svg";

export default function MicrosoftButton() {
    const [loginInProgress, setLoginInProgress] = useState<boolean>(false);

    const fetchLoginLink = () => {
        if(loginInProgress) return;

        setLoginInProgress(true);
        getMicrosoftLoginLink(
            Intl.DateTimeFormat().resolvedOptions().timeZone
        ).then(link => {
            window.location.href = link;
            setTimeout(() => {
                setLoginInProgress(false);
            }, 10000); // in case loading takes too long

        }).catch(err => {
            setLoginInProgress(false);
            toast.error("Failed to log in using Microsoft, try again later."); 
            console.error("MS login error: ", err);
        })
    }

    return (
        <button className="ms" onClick={fetchLoginLink}>
            <img src={MicrosoftIcon} />
            <strong>Log in with Microsoft</strong>

            <SpinnerCircular 
                enabled={loginInProgress}
                color="white"
                size="1.25em"
                style={{marginLeft: "1em"}}
            />
        </button>
    )
}