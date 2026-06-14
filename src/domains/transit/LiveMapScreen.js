import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Text, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import axios from 'axios';

const LiveMapScreen = () => {
    const [loading, setLoading] = useState(true);
    const [trips, setTrips] = useState([]);

    const fetchTrips = async () => {
        try {
            const response = await axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/passenger/live-trips/`, {
                headers: { Authorization: `Bearer ${global.userToken}` },
            });
            setTrips(response.data);
        } catch (error) {
            setTrips([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTrips();
        const interval = setInterval(fetchTrips, 10000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#00a8ff" />
                <Text style={styles.text}>Chargement des trajets actifs...</Text>
            </View>
        );
    }

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.title}>Suivi en direct</Text>
            <Text style={styles.text}>Position basée sur les stations du réseau.</Text>

            <TouchableOpacity style={styles.refreshButton} onPress={fetchTrips}>
                <Text style={styles.refreshText}>Actualiser</Text>
            </TouchableOpacity>

            {trips.length === 0 ? (
                <View style={styles.emptyCard}>
                    <Text style={styles.emptyText}>Aucun bus actif pour le moment.</Text>
                </View>
            ) : trips.map((trip) => (
                <View key={trip.id} style={styles.tripCard}>
                    <Text style={styles.busTitle}>Bus {trip.vehicle?.plate_number || 'N/A'}</Text>
                    <Text style={styles.routeText}>{trip.trajet?.name || 'Trajet'}</Text>
                    <Text style={styles.info}>Station actuelle: {trip.current_station?.name || 'N/A'}</Text>
                    <Text style={styles.info}>Prochaine station: {trip.next_station?.name || 'Aucune'}</Text>
                    <Text style={styles.info}>Destination: {trip.destination_station?.name || 'N/A'}</Text>
                    <Text style={[styles.status, trip.status === 'COMPLETED' && styles.completed]}>Statut: {trip.status}</Text>
                </View>
            ))}
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flexGrow: 1, padding: 20, backgroundColor: '#f5f6fa' },
    centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, backgroundColor: '#f5f6fa' },
    title: { fontSize: 30, fontWeight: 'bold', color: '#2f3640', marginBottom: 8, textAlign: 'center' },
    text: { fontSize: 16, color: '#718093', textAlign: 'center', marginBottom: 20 },
    refreshButton: { backgroundColor: '#00a8ff', padding: 14, borderRadius: 10, alignItems: 'center', marginBottom: 18 },
    refreshText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
    emptyCard: { backgroundColor: '#fff', borderRadius: 16, padding: 18 },
    emptyText: { color: '#718093', textAlign: 'center' },
    tripCard: { backgroundColor: '#fff', borderRadius: 16, padding: 18, marginBottom: 14, borderLeftWidth: 5, borderLeftColor: '#00a8ff' },
    busTitle: { fontSize: 21, color: '#2f3640', fontWeight: 'bold', marginBottom: 5 },
    routeText: { fontSize: 15, color: '#718093', marginBottom: 10 },
    info: { fontSize: 16, color: '#2f3640', marginBottom: 6 },
    status: { fontSize: 15, color: '#4cd137', fontWeight: 'bold', marginTop: 6 },
    completed: { color: '#718093' },
});

export default LiveMapScreen;
