/*
Type declarations for @react-native-picker/picker
*/

declare module "@react-native-picker/picker" {
  import { ComponentType } from "react";
  import { ViewProps } from "react-native";

  interface PickerItemProps {
    label: string;
    value: any;
    color?: string;
    enabled?: boolean;
  }

  interface PickerProps extends ViewProps {
    selectedValue?: any;
    onValueChange?: (itemValue: any, itemIndex: number) => void;
    enabled?: boolean;
    mode?: "dialog" | "dropdown";
    prompt?: string;
    testID?: string;
  }

  const Picker: {
    (props: PickerProps): JSX.Element;
    Item: ComponentType<PickerItemProps>;
  };

  export { Picker };
  export default Picker;
}
