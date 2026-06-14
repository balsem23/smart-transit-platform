export const getHomeRouteForRole = (role) => {
    switch (role) {
        case 'DRIVER':
            return 'DriverHome';
        case 'CONTROLLER':
            return 'ControllerHome';
        case 'ADMIN':
        case 'SUPER_ADMIN':
            return 'AdminHome';
        case 'PASSENGER':
        default:
            return 'PassengerHome';
    }
};

export const getRoleLabel = (role) => {
    switch (role) {
        case 'DRIVER':
            return 'Conducteur';
        case 'CONTROLLER':
            return 'Controleur';
        case 'ADMIN':
            return 'Administrateur';
        case 'SUPER_ADMIN':
            return 'Super Administrateur';
        case 'PASSENGER':
            return 'Passager';
        default:
            return role || 'Non disponible';
    }
};
