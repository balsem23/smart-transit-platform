import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator, ScrollView, TextInput } from 'react-native';
import axios from 'axios';
import AppLogo from '../../core/AppLogo';

const incidentTypes = [
    { label: 'Retard', value: 'DELAY' },
    { label: 'Panne', value: 'BREAKDOWN' },
    { label: 'Accident', value: 'ACCIDENT' },
    { label: 'Sécurité', value: 'SECURITY' },
    { label: 'Autre', value: 'OTHER' },
];

const DriverHomeScreen = ({ navigation }) => {
    const [loading, setLoading] = useState(true);
    const [trajets, setTrajets] = useState([]);
    const [selectedTrajetId, setSelectedTrajetId] = useState(null);
    const [departureStationId, setDepartureStationId] = useState(null);
    const [arrivalStationId, setArrivalStationId] = useState(null);
    const [session, setSession] = useState(null);
    const [upcoming, setUpcoming] = useState([]);
    const [incidents, setIncidents] = useState([]);
    const [incidentType, setIncidentType] = useState('DELAY');
    const [incidentDescription, setIncidentDescription] = useState('');

    const authHeaders = { Authorization: `Bearer ${global.userToken}` };

    const selectedTrajet = trajets.find(r => r.id === selectedTrajetId);
    const stations = selectedTrajet?.stations || [];

    const loadData = async () => {
        setLoading(true);
        try {
            const [setupRes, currentRes, incRes] = await Promise.all([
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/setup/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/current/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/incidents/`, { headers: authHeaders }),
            ]);
            setTrajets(setupRes.data.trajets || []);
            if (currentRes.data.active) {
                setSession(currentRes.data.active);
                setUpcoming(currentRes.data.upcoming_stations || []);
            }
            setIncidents(incRes.data || []);
        } catch (error) {
            Alert.alert('Erreur', 'Impossible de charger les données.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, []);

    const startJourney = async () => {
        if (!selectedTrajetId || !departureStationId || !arrivalStationId) {
            return Alert.alert('Erreur', 'Choisissez une route, un départ et une arrivée.');
        }
        try {
            const res = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/start/`, {
                trajet_id: selectedTrajetId,
                departure_station_id: departureStationId,
                arrival_station_id: arrivalStationId,
            }, { headers: authHeaders });
            setSession(res.data);
            setUpcoming(stations.filter(s => s.order_number >= res.data.current_order));
            Alert.alert('Trajet démarré', `Départ: ${res.data.departure_station.name}`);
        } catch (error) {
            Alert.alert('Erreur', error.response?.data?.detail || 'Impossible de démarrer.');
        }
    };

    const updateStation = async (stationId) => {
        try {
            const res = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/update-station/`,
                { station_id: stationId },
                { headers: authHeaders }
            );
            setSession(res.data);
            setUpcoming(stations.filter(s => s.order_number >= res.data.current_order));
            if (res.data.status === 'FINISHED') {
                Alert.alert('Trajet terminé', 'Arrivé à destination.');
            } else {
                Alert.alert('Station mise à jour', `Station actuelle: ${res.data.current_station.name}`);
            }
        } catch (error) {
            Alert.alert('Erreur', error.response?.data?.detail || 'Impossible de mettre à jour.');
        }
    };

    const finishJourney = async () => {
        try {
            const res = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/finish/`, {}, { headers: authHeaders });
            setSession(res.data);
            Alert.alert('Trajet terminé', 'Arrivé à destination.');
        } catch (error) {
            Alert.alert('Erreur', error.response?.data?.detail || 'Impossible de terminer.');
        }
    };

    const reportIncident = async () => {
        if (!incidentDescription.trim()) return Alert.alert('Erreur', 'Décrivez l\'incident.');
        try {
            await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/incidents/`, {
                type: incidentType,
                description: incidentDescription.trim(),
            }, { headers: authHeaders });
            setIncidentDescription('');
            const incRes = await axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/driver/incidents/`, { headers: authHeaders });
            setIncidents(incRes.data || []);
            Alert.alert('Incident signalé', 'Envoyé à l\'administration.');
        } catch (error) {
            Alert.alert('Erreur', 'Impossible de signaler l\'incident.');
        }
    };

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#4cd137" />
                <Text style={styles.loadingText}>Chargement...</Text>
            </View>
        );
    }

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <View style={styles.header}>
                <AppLogo size={84} />
                <Text style={styles.title}>Espace Conducteur</Text>
                <Text style={styles.subtitle}>Sélectionnez votre départ et arrivée sur un trajet.</Text>
            </View>

            {!session && (
                <>
                    <Text style={styles.sectionTitle}>1. Choisir le trajet</Text>
                    {trajets.length === 0 ? (
                        <View style={styles.emptyCard}><Text style={styles.emptyText}>Aucun trajet disponible.</Text></View>
                    ) : trajets.map(trajet => (
                        <TouchableOpacity key={trajet.id} style={[styles.card, selectedTrajetId === trajet.id && styles.cardActive]} onPress={() => { setSelectedTrajetId(trajet.id); setDepartureStationId(null); setArrivalStationId(null); }}>
                            <Text style={styles.cardTitle}>{trajet.name}</Text>
                            <Text style={styles.cardText}>{trajet.stations.map(s => s.station.name).join(' -> ')}</Text>
                        </TouchableOpacity>
                    ))}

                    {stations.length > 0 && (
                        <>
                            <Text style={styles.sectionTitle}>2. Station de départ</Text>
                            <View style={styles.stationGrid}>
                                {stations.map(s => (
                                    <TouchableOpacity key={s.station.id} style={[styles.stationBtn, departureStationId === s.station.id && styles.stationBtnActive]} onPress={() => setDepartureStationId(s.station.id)}>
                                        <Text style={[styles.stationBtnText, departureStationId === s.station.id && styles.stationBtnTextActive]}>{s.station.name}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>

                            <Text style={styles.sectionTitle}>3. Station d'arrivée</Text>
                            <View style={styles.stationGrid}>
                                {stations.filter(s => s.station.id !== departureStationId).map(s => (
                                    <TouchableOpacity key={s.station.id} style={[styles.stationBtn, arrivalStationId === s.station.id && styles.stationBtnActive]} onPress={() => setArrivalStationId(s.station.id)}>
                                        <Text style={[styles.stationBtnText, arrivalStationId === s.station.id && styles.stationBtnTextActive]}>{s.station.name}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>

                            <TouchableOpacity style={styles.primaryButton} onPress={startJourney}>
                                <Text style={styles.buttonText}>Démarrer le trajet</Text>
                            </TouchableOpacity>
                        </>
                    )}
                </>
            )}

            {session && (
                <View style={styles.actionCard}>
                    <Text style={styles.cardTitle}>{session.status === 'FINISHED' ? 'Trajet terminé' : 'Trajet en cours'}</Text>
                    <Text style={styles.cardText}>Trajet: {session.trajet?.name}</Text>
                    <Text style={styles.cardText}>Départ: {session.departure_station?.name}</Text>
                    <Text style={styles.cardText}>Arrivée: {session.arrival_station?.name}</Text>
                    <Text style={styles.cardText}>Station actuelle: {session.current_station?.name}</Text>
                    <Text style={styles.status}>Statut: {session.status === 'FINISHED' ? 'Terminé' : session.status}</Text>

                    {session.status !== 'FINISHED' && (
                        <>
                            <Text style={styles.sectionTitle}>Stations à venir</Text>
                            {upcoming.map(s => (
                                <View key={s.station.id} style={styles.upcomingItem}>
                                    <Text style={[styles.upcomingText, s.station.id === session.current_station?.id && styles.upcomingCurrent]}>
                                        {s.order_number}. {s.station.name}
                                        {s.station.id === session.current_station?.id ? ' (vous êtes ici)' : ''}
                                    </Text>
                                    {s.station.id !== session.current_station?.id && (
                                        <TouchableOpacity style={styles.arrivedBtn} onPress={() => updateStation(s.station.id)}>
                                            <Text style={styles.arrivedBtnText}>Arrivé</Text>
                                        </TouchableOpacity>
                                    )}
                                </View>
                            ))}

                            <TouchableOpacity style={styles.finishButton} onPress={finishJourney}>
                                <Text style={styles.buttonText}>Terminer le trajet</Text>
                            </TouchableOpacity>
                        </>
                    )}

                    {session.status === 'FINISHED' && (
                        <TouchableOpacity style={styles.primaryButton} onPress={() => { setSession(null); setUpcoming([]); setSelectedTrajetId(null); setDepartureStationId(null); setArrivalStationId(null); }}>
                            <Text style={styles.buttonText}>Nouveau trajet</Text>
                        </TouchableOpacity>
                    )}
                </View>
            )}

            <Text style={styles.sectionTitle}>Signaler un incident</Text>
            <View style={styles.actionCard}>
                <View style={styles.typeGrid}>
                    {incidentTypes.map(type => (
                        <TouchableOpacity key={type.value} style={[styles.typeButton, incidentType === type.value && styles.typeButtonActive]} onPress={() => setIncidentType(type.value)}>
                            <Text style={[styles.typeText, incidentType === type.value && styles.typeTextActive]}>{type.label}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
                <TextInput style={styles.textArea} placeholder="Décrire l'incident..." value={incidentDescription} onChangeText={setIncidentDescription} multiline />
                <TouchableOpacity style={styles.warningButton} onPress={reportIncident}>
                    <Text style={styles.buttonText}>Envoyer</Text>
                </TouchableOpacity>
            </View>

            {incidents.length > 0 && (
                <>
                    <Text style={styles.sectionTitle}>Mes incidents récents</Text>
                    {incidents.slice(0, 5).map(inc => (
                        <View key={inc.id} style={styles.incidentCard}>
                            <Text style={styles.cardTitle}>{inc.type}</Text>
                            <Text style={styles.cardText}>{inc.description}</Text>
                            <Text style={styles.status}>Statut: {inc.status}</Text>
                        </View>
                    ))}
                </>
            )}

            <TouchableOpacity style={styles.profileButton} onPress={() => navigation.navigate('Profile')}>
                <Text style={styles.profileButtonText}>Profil & statistiques</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.logoutButton} onPress={() => { global.userToken = null; global.currentUser = null; navigation.replace('Login'); }}>
                <Text style={styles.logoutButtonText}>Se déconnecter</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flexGrow: 1, padding: 20, backgroundColor: '#f5f6fa' },
    centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f5f6fa' },
    loadingText: { marginTop: 12, color: '#718093' },
    header: { alignItems: 'center', marginTop: 26, marginBottom: 24 },
    title: { fontSize: 30, fontWeight: 'bold', color: '#2f3640', marginTop: 12 },
    subtitle: { fontSize: 15, color: '#718093', textAlign: 'center', marginTop: 6 },
    sectionTitle: { fontSize: 20, fontWeight: 'bold', color: '#2f3640', marginBottom: 12, marginTop: 8 },
    emptyCard: { backgroundColor: '#fff', padding: 18, borderRadius: 16, marginBottom: 14 },
    emptyText: { color: '#718093', textAlign: 'center' },
    card: { backgroundColor: '#fff', padding: 18, borderRadius: 16, marginBottom: 14, borderLeftWidth: 5, borderLeftColor: '#dcdde1' },
    cardActive: { borderLeftColor: '#4cd137', backgroundColor: '#f0fff4' },
    actionCard: { backgroundColor: '#fff', padding: 18, borderRadius: 16, marginBottom: 18 },
    cardTitle: { fontSize: 19, fontWeight: 'bold', color: '#2f3640', marginBottom: 6 },
    cardText: { fontSize: 14, color: '#718093', lineHeight: 20 },
    status: { fontSize: 14, color: '#4cd137', fontWeight: 'bold', marginTop: 6 },
    stationGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
    stationBtn: { backgroundColor: '#dfe6e9', paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10 },
    stationBtnActive: { backgroundColor: '#4cd137' },
    stationBtnText: { fontWeight: 'bold', color: '#2f3640' },
    stationBtnTextActive: { color: '#fff' },
    upcomingItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
    upcomingText: { fontSize: 15, color: '#2f3640', flex: 1 },
    upcomingCurrent: { fontWeight: 'bold', color: '#4cd137' },
    arrivedBtn: { backgroundColor: '#00a8ff', paddingVertical: 6, paddingHorizontal: 14, borderRadius: 8 },
    arrivedBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 13 },
    buttonRow: { flexDirection: 'row', gap: 10, marginTop: 14 },
    primaryButton: { backgroundColor: '#4cd137', padding: 14, borderRadius: 10, alignItems: 'center', marginTop: 10 },
    finishButton: { backgroundColor: '#e84118', padding: 14, borderRadius: 10, alignItems: 'center', flex: 1 },
    buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
    warningButton: { backgroundColor: '#e1b12c', padding: 14, borderRadius: 10, alignItems: 'center', marginTop: 10 },
    typeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
    typeButton: { backgroundColor: '#f5f6fa', borderRadius: 10, paddingVertical: 10, paddingHorizontal: 12 },
    typeButtonActive: { backgroundColor: '#4cd137' },
    typeText: { color: '#2f3640', fontWeight: '700' },
    typeTextActive: { color: '#fff' },
    textArea: { backgroundColor: '#f5f6fa', borderRadius: 10, padding: 14, minHeight: 92, textAlignVertical: 'top', fontSize: 15 },
    incidentCard: { backgroundColor: '#fff', padding: 16, borderRadius: 14, marginBottom: 12, borderLeftWidth: 5, borderLeftColor: '#e1b12c' },
    profileButton: { backgroundColor: '#fff', padding: 16, borderRadius: 12, alignItems: 'center', borderWidth: 1, borderColor: '#dcdde1', marginTop: 8 },
    profileButtonText: { color: '#2f3640', fontSize: 16, fontWeight: 'bold' },
    logoutButton: { backgroundColor: '#fff', padding: 16, borderRadius: 12, alignItems: 'center', borderWidth: 1, borderColor: '#e84118', marginTop: 12, marginBottom: 20 },
    logoutButtonText: { color: '#e84118', fontSize: 16, fontWeight: 'bold' },
});

export default DriverHomeScreen;
