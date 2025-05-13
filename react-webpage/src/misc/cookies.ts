export interface CookieOpts {
    domain?: string,
    path?: string,
    secure?: boolean,
    samesite?: "Strict" | "Lax" | "None"
}

export function getCookie(name: string): string | undefined {
    let cookies: string[] = document.cookie.split(";");
    for(const cookie of cookies) {
        if(cookie.trim().startsWith(name)) {
            let value = cookie.split("=")[1];
            return value;
        } 
    }
}

export function removeCookie(name: string, opts: CookieOpts = {}) {
    let newValue = `${name}=; expires=Thu, 01 Jan 1970 00:00:01 GMT`;
    if(opts.domain)
        newValue += `; Domain=${opts.domain}`;

    if(opts.path)
        newValue += `; Path=${opts.path}`;

    if(opts.secure)
        newValue += "; Secure";

    if(opts.samesite)
        newValue += `; SameSite=${opts.samesite}`;

    document.cookie = newValue;
}