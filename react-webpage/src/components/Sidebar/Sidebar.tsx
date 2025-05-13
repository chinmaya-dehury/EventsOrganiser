import { useState } from 'react';
import { LuCalendarDays } from "react-icons/lu";
import { IoMenu, IoSettingsOutline } from "react-icons/io5";
import { MdLogout } from "react-icons/md";
import useFitText from "use-fit-text";
import { NavLink } from "react-router";
import { jwtDecode } from 'jwt-decode';

import "./sidebar.scss"
import "./sidebar-nav.scss";
import { JWTData } from '@/interfaces/global_interfaces';
import { useAccountDataStore } from '@/hooks';
import { getCookie, removeCookie } from '@/misc/cookies';

function Sidebar() {
	const { fontSize, ref } = useFitText();
	const { setAuthenticated} = useAccountDataStore();
	const [isClosed, setIsClosed] = useState<Boolean>(true);
	const jwt = getCookie(import.meta.env.VITE__JWT_COOKIE_NAME);

	const logOut = () => {
		removeCookie(import.meta.env.VITE__JWT_COOKIE_NAME, {
			path: "/",
			secure: true,
			samesite: "Lax"
		});
		setAuthenticated(false);
	}

	let userEmail = "";
	try {
		if(jwt) {
			const decoded: JWTData = jwtDecode(jwt);
			userEmail = decoded.sub;
		}
	} catch(e) {} // this isn't supposed to happen unless the JWT has been tampered with

	let sidebarClassname: string = "sidebar";
	if(isClosed)
		sidebarClassname += " closed";

	return (
		<>			
			<div className="sidebar-header header-mobile">
				<IoMenu style={{cursor: "pointer"}} onClick={() => setIsClosed(prev => !prev)}/>

				<span style={{flexGrow: "1"}}>Events Organiser</span>
			</div>

			<div style={{position: "relative"}}>
				<aside className={sidebarClassname}>
					<div className="sidebar-header">
						<span>Events Organiser</span>
					</div>

					<div className="sidebar-content">
						<NavLink to="/" className="sidebar-link"> 
							<LuCalendarDays className="sidebar-btn-icon"/>
							<span>Events</span>
						</NavLink>

						<NavLink to="/settings" className="sidebar-link"> 
							<IoSettingsOutline className="sidebar-btn-icon"/>
							<span>Settings</span>
						</NavLink>
					</div>

					<div className="sidebar-footer" style={{padding: "1rem"}}>
						<div ref={ref} style={{ fontSize }}>
							<b>{userEmail}</b>
						</div>
						<a href="#" className="logout-btn" onClick={logOut}>
							<MdLogout />
							Log out
						</a>
					</div>
				</aside>
			</div>
		</>
	)
}

export default Sidebar;
