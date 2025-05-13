import { useEffect } from 'react'
import { Route, Routes, Navigate, Outlet, NavigateFunction } from 'react-router';
import { jwtDecode } from "jwt-decode";
import { ToastContainer } from 'react-toastify';

import { Sidebar } from './components';
import HomePage from './pages/home';
import { useNavigate } from "react-router";
import { EventTag, JWTData } from './interfaces/global_interfaces';
import { useEventsStore, useAccountDataStore } from './hooks';

import { getTags } from './apis/events';
import LoginPage from './pages/login';
import SettingsPage from './pages/settings';
import { getCookie, removeCookie } from './misc/cookies';

async function fetchTags(setTags: (t: EventTag[]) => void, retryAttempt: number = 0) {
	getTags().then(result => {
		setTags(result);
	}).catch(err => {
		if(retryAttempt > 5) return;

		setTimeout(() => {
			console.log(`Retrying tags fetch (${retryAttempt+1})`);
			console.error("Tag fetching error", err);
			fetchTags(setTags, retryAttempt+1);
		}, 5000);
	})
}

function init(
	setTags: (t: EventTag[]) => void, 
	setAuthenticated: (a: boolean) => void,
	navigate: NavigateFunction,
) {
		fetchTags(setTags);
		
		const jwt = getCookie(import.meta.env.VITE__JWT_COOKIE_NAME);
		if(!jwt) return;

		try {
			const decoded: JWTData = jwtDecode(jwt);
			if(Date.now() > decoded.exp * 1000)
				throw new Error("auth expired");

			setAuthenticated(true);
			navigate("/");

			const autoLogout = setTimeout(() => {
				setAuthenticated(false);
				removeCookie(import.meta.env.VITE__JWT_COOKIE_NAME);
			}, decoded.exp*1000-Date.now());

			return () => {
				clearTimeout(autoLogout);
			}
		} catch(e) {
			removeCookie(import.meta.env.VITE__JWT_COOKIE_NAME);
			navigate("/login");
		}
}

// https://medium.com/@dennisivy/creating-protected-routes-with-react-router-v6-2c4bbaf7bc1c
const ProtectedRoute = () => {
	const {authenticated} = useAccountDataStore();
	return (
		authenticated ? <Outlet/> : <Navigate to="/login"/>
	)
}

function App() {
	const {authenticated, setAuthenticated} = useAccountDataStore();
	const {setTags} = useEventsStore();
	const navigate = useNavigate();

	useEffect(() => {
		return init(
			setTags, 
			setAuthenticated, 
			navigate, 
		);
	}, []);

	let sidebar = <nav></nav>;
	if(authenticated)
		sidebar = <nav><Sidebar /></nav>;

	return (
		<>
			{sidebar}
			<main>
				<ToastContainer/>
				<Routes>
					<Route element={<ProtectedRoute/>}>
						<Route path="/" element={<HomePage/>} />
						<Route path="/settings" element={<SettingsPage />} />
					</Route>

					<Route path="/login" element={<LoginPage/>} />

					<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</main>
		</>
	)
}

export default App;
