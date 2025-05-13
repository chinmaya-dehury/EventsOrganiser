import { ReactNode, ComponentProps } from "react";

import "./input-with-icon.css";

interface ElementProps extends ComponentProps<"input"> {
    children: ReactNode
}

function InputWithIcon({ children, ...props }: ElementProps) {
    return (
        <div className="input-with-icon">
            <input {...props} />
            {children}
        </div>
    );
}

export default InputWithIcon;