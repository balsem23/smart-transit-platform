import React from 'react';
import Svg, { Circle, Path, Rect } from 'react-native-svg';

const AppLogo = ({ size = 96 }) => (
    <Svg width={size} height={size} viewBox="0 0 96 96">
        <Circle cx="48" cy="48" r="46" fill="#00A8FF" />
        <Circle cx="48" cy="48" r="36" fill="#F5F6FA" />
        <Path d="M28 56c0-16 8-26 20-26s20 10 20 26" fill="none" stroke="#00A8FF" strokeWidth="7" strokeLinecap="round" />
        <Rect x="30" y="48" width="36" height="20" rx="6" fill="#2F3640" />
        <Circle cx="39" cy="70" r="5" fill="#2F3640" />
        <Circle cx="57" cy="70" r="5" fill="#2F3640" />
        <Path d="M38 42h20" stroke="#00A8FF" strokeWidth="5" strokeLinecap="round" />
    </Svg>
);

export default AppLogo;
