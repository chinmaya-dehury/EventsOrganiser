import { useNavigate, useSearchParams } from "react-router";

import MicrosoftButton from "./components/MicrosoftButton";
import "./login.css";
import { useAccountDataStore } from "@/hooks";
import { useEffect } from "react";
import { toast } from "react-toastify";


export default function LoginPage() {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const {authenticated} = useAccountDataStore();

    useEffect(() => {
        if(authenticated) navigate("/");

        if(searchParams.get("error")) {
            toast.error(`Failed to log in: ${searchParams.get("error")}`)
            setSearchParams(new URLSearchParams());
        }
    })

    return (
        <div className="login-flexbox">
            <div>
                <div className="login-header">
                    <h1>Events Organiser</h1>
                    <span>You need to log in to use this application</span>
                </div>
                <div className="login-btns">
                    <MicrosoftButton />
                </div>
            </div>
        </div>
    )
}