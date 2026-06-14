import React from 'react';
import { ScrollView, Text, StyleSheet, TouchableOpacity, View } from 'react-native';
import AppLogo from '../../core/AppLogo';

const PassengerHomeScreen = ({ navigation }) => {
    const handleLogout = () => {
        global.userToken = null;
        global.currentUser = null;
        navigation.replace('Login');
    };

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                <Text style={styles.logoutText}>Se déconnecter</Text>
            </TouchableOpacity>

            <View style={styles.header}>
                <AppLogo size={84} />
                <Text style={styles.title}>Espace Passager</Text>
                <Text style={styles.subtitle}>Achetez, suivez et validez vos titres de transport.</Text>
            </View>

            <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('Wallet')}>
                <Text style={styles.cardTitle}>Wallet & Paiement</Text>
                <Text style={styles.cardText}>Consulter le solde, acheter un ticket ou abonnement.</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('LiveMap')}>
                <Text style={styles.cardTitle}>Suivi en temps réel</Text>
                <Text style={styles.cardText}>Voir les véhicules et les estimations d'arrivée.</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('Profile')}>
                <Text style={styles.cardTitle}>Profil</Text>
                <Text style={styles.cardText}>Consulter vos informations personnelles.</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.logoutBottom} onPress={handleLogout}>
                <Text style={styles.logoutBottomText}>Se déconnecter</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flexGrow: 1, padding: 20, backgroundColor: '#f5f6fa' },
    header: { alignItems: 'center', marginTop: 10, marginBottom: 24 },
    title: { fontSize: 30, fontWeight: 'bold', color: '#2f3640', marginTop: 12 },
    subtitle: { fontSize: 15, color: '#718093', textAlign: 'center', marginTop: 6 },
    card: { backgroundColor: '#fff', padding: 18, borderRadius: 16, marginBottom: 14, borderLeftWidth: 5, borderLeftColor: '#00a8ff' },
    cardTitle: { fontSize: 19, fontWeight: 'bold', color: '#2f3640', marginBottom: 6 },
    cardText: { fontSize: 14, color: '#718093', lineHeight: 20 },
    logoutButton: { alignSelf: 'flex-end', padding: 8 },
    logoutText: { color: '#e84118', fontWeight: 'bold' },
    logoutBottom: { backgroundColor: '#fff', padding: 16, borderRadius: 12, alignItems: 'center', borderWidth: 1, borderColor: '#e84118', marginTop: 8, marginBottom: 20 },
    logoutBottomText: { color: '#e84118', fontSize: 16, fontWeight: 'bold' },
});

export default PassengerHomeScreen;
