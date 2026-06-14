import React, { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import axios from 'axios';

const AdminNetworkScreen = () => {
    const [lines, setLines] = useState([]);
    const [stations, setStations] = useState([]);
    const [buses, setBuses] = useState([]);
    const [trajets, setTrajets] = useState([]);
    const [trajetStations, setTrajetStations] = useState([]);
    const [importedStations, setImportedStations] = useState([]);
    const [importedRoutes, setImportedRoutes] = useState([]);
    const [importSummary, setImportSummary] = useState({});
    const [gtfsImporting, setGtfsImporting] = useState(false);
    const [osmFetching, setOsmFetching] = useState(false);
    const [fetchCity, setFetchCity] = useState('');
    const [fetchType, setFetchType] = useState('BUS');
    const [selectedTab, setSelectedTab] = useState('stations');
    const [editItem, setEditItem] = useState(null);
    const [editName, setEditName] = useState('');

    const authHeaders = { Authorization: `Bearer ${global.userToken}` };

    const fetchAll = async () => {
        try {
            const [linesRes, stationsRes, busesRes, trajetsRes, tsRes, isRes, irRes, sumRes] = await Promise.all([
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/lines/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/stations/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/buses/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/trajets/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/trajet-stations/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/imported-stations/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/imported-routes/`, { headers: authHeaders }),
                axios.get(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/import-summary/`, { headers: authHeaders }),
            ]);
            setLines(linesRes.data.results || linesRes.data || []);
            setStations(stationsRes.data.results || stationsRes.data || []);
            setBuses(busesRes.data.results || busesRes.data || []);
            setTrajets(trajetsRes.data.results || trajetsRes.data || []);
            setTrajetStations(tsRes.data.results || tsRes.data || []);
            setImportedStations(isRes.data.results || isRes.data || []);
            setImportedRoutes(irRes.data.results || irRes.data || []);
            setImportSummary(sumRes.data || {});
        } catch (e) {
            Alert.alert('Erreur', 'Impossible de charger les données réseau.');
        }
    };

    useEffect(() => { fetchAll(); }, []);

    const syncGtfs = async () => {
        setGtfsImporting(true);
        try {
            const res = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/gtfs-sync/`, {}, { headers: authHeaders });
            Alert.alert('Synchronisation réussie', `${res.data.created.stations_total} stations, ${res.data.created.routes_total} routes importées.`);
            fetchAll();
        } catch (error) {
            Alert.alert('Erreur', error.response?.data?.detail || 'Échec de la synchronisation TRANSTU.');
        } finally {
            setGtfsImporting(false);
        }
    };

    const fetchOsmStations = async () => {
        if (!fetchCity.trim()) return Alert.alert('Erreur', 'Veuillez entrer une ville.');
        setOsmFetching(true);
        try {
            const res = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/fetch-stations/`,
                { city: fetchCity.trim(), station_type: fetchType },
                { headers: authHeaders }
            );
            Alert.alert('Stations récupérées', `${res.data.created} créées, ${res.data.updated} mises à jour, ${res.data.skipped} ignorées.`);
            fetchAll();
        } catch (error) {
            Alert.alert('Erreur', error.response?.data?.detail || 'Échec de la récupération.');
        } finally {
            setOsmFetching(false);
        }
    };

    const promoteStations = async () => {
        const pending = importedStations.filter(s => !s.is_approved);
        if (pending.length === 0) return Alert.alert('Info', 'Aucune station en attente.');
        try {
            const res = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/promote-stations/`,
                { imported_station_ids: pending.map(s => s.id) },
                { headers: authHeaders }
            );
            Alert.alert('Succès', res.data.detail);
            fetchAll();
        } catch (e) {
            Alert.alert('Erreur', 'Impossible de promouvoir les stations.');
        }
    };

    const promoteRoutes = async () => {
        const pending = importedRoutes.filter(r => !r.is_approved);
        if (pending.length === 0) return Alert.alert('Info', 'Aucune route en attente.');
        try {
            const res = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/transit/admin/promote-routes/`,
                { imported_route_ids: pending.map(r => r.id) },
                { headers: authHeaders }
            );
            Alert.alert('Succès', res.data.detail);
            fetchAll();
        } catch (e) {
            Alert.alert('Erreur', 'Impossible de promouvoir les routes.');
        }
    };

    const deleteItem = async (model, id) => {
        const endpoints = {
            station: `${process.env.EXPO_PUBLIC_API_URL}/transit/stations/${id}/`,
            line: `${process.env.EXPO_PUBLIC_API_URL}/transit/admin/lines/${id}/`,
            bus: `${process.env.EXPO_PUBLIC_API_URL}/transit/admin/buses/${id}/`,
            trajet: `${process.env.EXPO_PUBLIC_API_URL}/transit/admin/trajets/${id}/`,
        };
        try {
            await axios.delete(endpoints[model], { headers: authHeaders });
            fetchAll();
        } catch (e) {
            Alert.alert('Erreur', 'Impossible de supprimer.');
        }
    };

    const updateName = async (model, id) => {
        if (!editName.trim()) return;
        const endpoints = {
            station: `${process.env.EXPO_PUBLIC_API_URL}/transit/stations/${id}/`,
            line: `${process.env.EXPO_PUBLIC_API_URL}/transit/admin/lines/${id}/`,
            bus: `${process.env.EXPO_PUBLIC_API_URL}/transit/admin/buses/${id}/`,
            trajet: `${process.env.EXPO_PUBLIC_API_URL}/transit/admin/trajets/${id}/`,
        };
        try {
            await axios.patch(endpoints[model], { name: editName.trim() }, { headers: authHeaders });
            setEditItem(null);
            setEditName('');
            fetchAll();
        } catch (e) {
            Alert.alert('Erreur', 'Impossible de modifier.');
        }
    };

    const tabs = ['stations', 'lignes', 'bus', 'trajets', 'import'];

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.title}>Réseau transport</Text>

            <View style={styles.syncRow}>
                <TouchableOpacity style={styles.syncButton} onPress={syncGtfs} disabled={gtfsImporting}>
                    <Text style={styles.buttonText}>{gtfsImporting ? '...' : 'TRANSTU'}</Text>
                </TouchableOpacity>
                <TextInput style={styles.cityInput} placeholder="Ville" value={fetchCity} onChangeText={setFetchCity} />
                <View style={styles.typeRow}>
                    {['BUS', 'METRO', 'TRAIN'].map(t => (
                        <TouchableOpacity key={t} style={[styles.typeBtn, fetchType === t && styles.typeBtnActive]} onPress={() => setFetchType(t)}>
                            <Text style={[styles.typeBtnText, fetchType === t && styles.typeBtnTextActive]}>{t}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
                <TouchableOpacity style={styles.syncButtonAlt} onPress={fetchOsmStations} disabled={osmFetching}>
                    <Text style={styles.buttonText}>{osmFetching ? '...' : 'OSM'}</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.tabRow}>
                {tabs.map(tab => (
                    <TouchableOpacity key={tab} style={[styles.tab, selectedTab === tab && styles.tabActive]} onPress={() => setSelectedTab(tab)}>
                        <Text style={[styles.tabText, selectedTab === tab && styles.tabTextActive]}>{tab}</Text>
                    </TouchableOpacity>
                ))}
            </View>

            {selectedTab === 'stations' && stations.length === 0 && <Text style={styles.empty}>Aucune station.</Text>}
            {selectedTab === 'stations' && stations.map(s => (
                <View key={s.id} style={styles.item}>
                    {editItem === s.id ? (
                        <View style={styles.editRow}>
                            <TextInput style={styles.editInput} value={editName} onChangeText={setEditName} />
                            <TouchableOpacity onPress={() => updateName('station', s.id)}><Text style={styles.saveBtn}>OK</Text></TouchableOpacity>
                            <TouchableOpacity onPress={() => setEditItem(null)}><Text style={styles.cancelBtn}>X</Text></TouchableOpacity>
                        </View>
                    ) : (
                        <View style={styles.itemRow}>
                            <Text style={styles.itemText}>{s.name} ({s.location_lat?.toFixed(3)},{s.location_lng?.toFixed(3)})</Text>
                            <View style={styles.itemActions}>
                                <TouchableOpacity onPress={() => { setEditItem(s.id); setEditName(s.name); }}><Text style={styles.editBtn}>R</Text></TouchableOpacity>
                                <TouchableOpacity onPress={() => deleteItem('station', s.id)}><Text style={styles.deleteBtn}>X</Text></TouchableOpacity>
                            </View>
                        </View>
                    )}
                </View>
            ))}

            {selectedTab === 'lignes' && lines.length === 0 && <Text style={styles.empty}>Aucune ligne.</Text>}
            {selectedTab === 'lignes' && lines.map(l => (
                <View key={l.id} style={styles.item}>
                    {editItem === l.id ? (
                        <View style={styles.editRow}>
                            <TextInput style={styles.editInput} value={editName} onChangeText={setEditName} />
                            <TouchableOpacity onPress={() => updateName('line', l.id)}><Text style={styles.saveBtn}>OK</Text></TouchableOpacity>
                            <TouchableOpacity onPress={() => setEditItem(null)}><Text style={styles.cancelBtn}>X</Text></TouchableOpacity>
                        </View>
                    ) : (
                        <View style={styles.itemRow}>
                            <Text style={styles.itemText}>{l.name} ({l.color_code})</Text>
                            <View style={styles.itemActions}>
                                <TouchableOpacity onPress={() => { setEditItem(l.id); setEditName(l.name); }}><Text style={styles.editBtn}>R</Text></TouchableOpacity>
                                <TouchableOpacity onPress={() => deleteItem('line', l.id)}><Text style={styles.deleteBtn}>X</Text></TouchableOpacity>
                            </View>
                        </View>
                    )}
                </View>
            ))}

            {selectedTab === 'bus' && buses.length === 0 && <Text style={styles.empty}>Aucun bus.</Text>}
            {selectedTab === 'bus' && buses.map(b => (
                <View key={b.id} style={styles.item}>
                    <View style={styles.itemRow}>
                        <Text style={styles.itemText}>{b.plate_number} ({b.fleet_id}) cap:{b.capacity}</Text>
                        <TouchableOpacity onPress={() => deleteItem('bus', b.id)}><Text style={styles.deleteBtn}>X</Text></TouchableOpacity>
                    </View>
                </View>
            ))}

            {selectedTab === 'trajets' && (
                <>
                    {trajets.length === 0 && <Text style={styles.empty}>Aucun trajet.</Text>}
                    {trajets.map(t => (
                        <View key={t.id} style={styles.item}>
                            {editItem === t.id ? (
                                <View style={styles.editRow}>
                                    <TextInput style={styles.editInput} value={editName} onChangeText={setEditName} />
                                    <TouchableOpacity onPress={() => updateName('trajet', t.id)}><Text style={styles.saveBtn}>OK</Text></TouchableOpacity>
                                    <TouchableOpacity onPress={() => setEditItem(null)}><Text style={styles.cancelBtn}>X</Text></TouchableOpacity>
                                </View>
                            ) : (
                                <View style={styles.itemRow}>
                                    <Text style={styles.itemText}>{t.name}</Text>
                                    <View style={styles.itemActions}>
                                        <TouchableOpacity onPress={() => { setEditItem(t.id); setEditName(t.name); }}><Text style={styles.editBtn}>R</Text></TouchableOpacity>
                                        <TouchableOpacity onPress={() => deleteItem('trajet', t.id)}><Text style={styles.deleteBtn}>X</Text></TouchableOpacity>
                                    </View>
                                </View>
                            )}
                        </View>
                    ))}
                    {trajetStations.length > 0 && (
                        <View style={styles.routeStationList}>
                            <Text style={styles.sectionTitle}>Stations ordonnées:</Text>
                            {trajetStations.map(ts => (
                                <Text key={ts.id} style={styles.rsText}>{ts.order_number}. trajet_id={ts.trajet} station_id={ts.station}</Text>
                            ))}
                        </View>
                    )}
                </>
            )}

            {selectedTab === 'import' && (
                <>
                    <Text style={styles.sectionTitle}>Import en attente</Text>
                    <View style={styles.importSummaryCard}>
                        <Text style={styles.summaryText}>Stations importées: {importSummary.imported_stations || 0}</Text>
                        <Text style={styles.summaryText}>Routes importées: {importSummary.imported_routes || 0}</Text>
                        <Text style={styles.summaryText}>Stations en attente: {importSummary.pending_stations || 0}</Text>
                        <Text style={styles.summaryText}>Routes en attente: {importSummary.pending_routes || 0}</Text>
                        <Text style={styles.summaryText}>Production: {importSummary.stations || 0} stations, {importSummary.trajets || 0} trajets</Text>
                    </View>

                    <View style={styles.promoteRow}>
                        <TouchableOpacity style={styles.promoteButton} onPress={promoteStations}>
                            <Text style={styles.buttonText}>Promouvoir stations</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={styles.promoteButton} onPress={promoteRoutes}>
                            <Text style={styles.buttonText}>Promouvoir routes</Text>
                        </TouchableOpacity>
                    </View>

                    <Text style={styles.sectionTitle}>Stations importées (OSM/GTFS)</Text>
                    {importedStations.length === 0 && <Text style={styles.empty}>Aucune station importée.</Text>}
                    {importedStations.map(s => (
                        <View key={s.id} style={[styles.item, s.is_approved && styles.itemApproved]}>
                            <View style={styles.itemRow}>
                                <Text style={styles.itemText}>{s.name} [{s.source}] {s.is_approved ? '✓' : '⏳'}</Text>
                            </View>
                        </View>
                    ))}

                    <Text style={styles.sectionTitle}>Routes importées (GTFS)</Text>
                    {importedRoutes.length === 0 && <Text style={styles.empty}>Aucune route importée.</Text>}
                    {importedRoutes.map(r => (
                        <View key={r.id} style={[styles.item, r.is_approved && styles.itemApproved]}>
                            <View style={styles.itemRow}>
                                <Text style={styles.itemText}>{r.name} [{r.source}] {r.is_approved ? '✓' : '⏳'}</Text>
                            </View>
                        </View>
                    ))}
                </>
            )}

            <Text style={styles.summary}>{stations.length} stations, {lines.length} lignes, {buses.length} bus, {trajets.length} trajets</Text>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { padding: 20, backgroundColor: '#f5f6fa' },
    title: { fontSize: 30, fontWeight: 'bold', color: '#2f3640', textAlign: 'center', marginBottom: 16 },
    syncRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16, alignItems: 'center' },
    syncButton: { backgroundColor: '#00b894', padding: 10, borderRadius: 8 },
    syncButtonAlt: { backgroundColor: '#0984e3', padding: 10, borderRadius: 8 },
    buttonText: { color: '#fff', fontWeight: 'bold' },
    cityInput: { backgroundColor: '#fff', borderRadius: 8, padding: 10, flex: 1, minWidth: 80 },
    typeRow: { flexDirection: 'row', gap: 4 },
    typeBtn: { backgroundColor: '#dfe6e9', padding: 8, borderRadius: 6 },
    typeBtnActive: { backgroundColor: '#0984e3' },
    typeBtnText: { fontWeight: 'bold', color: '#2f3640' },
    typeBtnTextActive: { color: '#fff' },
    tabRow: { flexDirection: 'row', gap: 6, marginBottom: 12 },
    tab: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 20, backgroundColor: '#dfe6e9' },
    tabActive: { backgroundColor: '#8c7ae6' },
    tabText: { fontWeight: 'bold', color: '#2f3640' },
    tabTextActive: { color: '#fff' },
    empty: { color: '#718093', textAlign: 'center', marginVertical: 20 },
    item: { backgroundColor: '#fff', borderRadius: 12, padding: 12, marginBottom: 8, borderLeftWidth: 4, borderLeftColor: '#8c7ae6' },
    itemApproved: { borderLeftColor: '#4cd137', opacity: 0.7 },
    itemRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    itemText: { fontSize: 14, color: '#2f3640', flex: 1 },
    itemActions: { flexDirection: 'row', gap: 8 },
    editBtn: { color: '#0984e3', fontWeight: 'bold' },
    deleteBtn: { color: '#e84118', fontWeight: 'bold' },
    editRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
    editInput: { backgroundColor: '#f5f6fa', borderRadius: 6, padding: 8, flex: 1 },
    saveBtn: { color: '#00b894', fontWeight: 'bold' },
    cancelBtn: { color: '#718093', fontWeight: 'bold' },
    routeStationList: { backgroundColor: '#fff', borderRadius: 12, padding: 12, marginTop: 8 },
    sectionTitle: { fontWeight: 'bold', color: '#2f3640', marginBottom: 6 },
    rsText: { fontSize: 12, color: '#636e72', marginBottom: 2 },
    summary: { color: '#718093', textAlign: 'center', marginVertical: 16 },
    importSummaryCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12 },
    summaryText: { fontSize: 14, color: '#2f3640', marginBottom: 4 },
    promoteRow: { flexDirection: 'row', gap: 10, marginBottom: 16 },
    promoteButton: { backgroundColor: '#00b894', padding: 12, borderRadius: 10, flex: 1, alignItems: 'center' },
});

export default AdminNetworkScreen;
