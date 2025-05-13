import Select, { ControlProps, CSSObjectWithLabel, Props, GroupBase, ContainerProps } from "react-select";

function CustomSelect<Option, IsMulti extends boolean = boolean, Group extends GroupBase<Option> = GroupBase<Option>>({ ...props }: Props<Option, IsMulti, Group>) {
    const styles = {
        container: (base: CSSObjectWithLabel, _: ContainerProps<Option, IsMulti, Group>): CSSObjectWithLabel => ({ 
            ...base,
            margin: "0.5rem"
        }),
        control: (base: CSSObjectWithLabel, props: ControlProps<Option, IsMulti, Group>): CSSObjectWithLabel => ({
            ...base,
            borderRadius: "1rem",
            borderColor: props.isFocused ? "var(--color-input-border-focused) !important" :"#CBD5E1",
            boxShadow: props.isFocused ? "0 0 0 0.25rem var(--color-input-outline-focused)" : base.boxShadow,

            ":hover": { // this actually means focused
                borderColor: "var(--color-input-border-hovered)"
            },
        })
    }

    return (
        <Select 
            {...props}
            styles={styles}
        />
    );
}

export default CustomSelect;