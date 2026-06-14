import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import AppLogo from '../../core/AppLogo';
import { getHomeRouteForRole, getRoleLabel } from '../../core/roleNavigation';

const ProfileScreen = ({ navigation }) => {
    const user = global.currentUser || {};

    const handleLogout = () => {
        global.userToken = null;
        global.currentUser = null;
        navigation.replace('Login');
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <AppLogo size={88} />
                <Text style={styles.title}>Mon Profil</Text>
                <Text style={styles.subtitle}>Bienvenue sur SITP</Text>
            </View>

            <View style={styles.card}>
                <Text style={styles.label}>Nom</Text>
                <Text style={styles.value}>{`${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Non disponible'}</Text>

                <Text style={styles.label}>Email</Text>
                <Text style={styles.value}>{user.email || 'Non disponible'}</Text>

                <Text style={styles.label}>Téléphone</Text>
                <Text style={styles.value}>{user.phone_number || 'Non disponible'}</Text>

                <Text style={styles.label}>Rôle</Text>
                <Text style={styles.value}>{getRoleLabel(user.role)}</Text>

                <Text style={styles.label}>Identifiant</Text>
                <Text style={styles.valueSmall}>{user.user_id || 'Non disponible'}</Text>
            </View>

            <TouchableOpacity style={styles.primaryButton} onPress={() => navigation.navigate(getHomeRouteForRole(user.role))}>
                <Text style={styles.primaryButtonText}>Retour à mon espace</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.secondaryButton} onPress={handleLogout}>
                <Text style={styles.secondaryButtonText}>Se déconnecter</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: '#f5f6fa' },
    header: { alignItems: 'center', marginTop: 35, marginBottom: 28 },
    title: { fontSize: 32, fontWeight: 'bold', color: '#2f3640', marginTop: 12 },
    subtitle: { fontSize: 16, color: '#718093', marginTop: 4 },
    card: { backgroundColor: '#fff', borderRadius: 18, padding: 20, marginBottom: 22 },
    label: { fontSize: 13, color: '#718093', fontWeight: '700', textTransform: 'uppercase', marginTop: 12 },
    value: { fontSize: 20, color: '#2f3640', fontWeight: '700', marginTop: 5 },
    valueSmall: { fontSize: 13, color: '#2f3640', marginTop: 5 },
    primaryButton: { backgroundColor: '#00a8ff', padding: 16, borderRadius: 12, alignItems: 'center', marginBottom: 12 },
    primaryButtonText: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
    secondaryButton: { backgroundColor: '#fff', padding: 16, borderRadius: 12, alignItems: 'center', borderWidth: 1, borderColor: '#dcdde1' },
    secondaryButtonText: { color: '#e84118', fontSize: 16, fontWeight: 'bold' },
});

export default ProfileScreen;
