import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import axios from 'axios';
import AppLogo from '../../core/AppLogo';
import { getHomeRouteForRole } from '../../core/roleNavigation';

const LoginScreen = ({ navigation }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async () => {
        try {
            const response = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/auth/login/`, {
                email: email.trim().toLowerCase(),
                password: password,
                device_id: 'device-003-passenger'
            });

            const token = response.data.access;
            global.userToken = token;
            global.currentUser = {
                user_id: response.data.user_id,
                role: response.data.role,
                email: response.data.email,
                phone_number: response.data.phone_number,
                first_name: response.data.first_name,
                last_name: response.data.last_name,
            };
            navigation.replace(getHomeRouteForRole(response.data.role));
        } catch (error) {
            const msg = error.response?.data?.detail || error.response?.data?.error || "Identifiants invalides";
            Alert.alert("Erreur", msg);
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.brand}>
                <AppLogo size={104} />
                <Text style={styles.appName}>SITP</Text>
                <Text style={styles.subtitle}>Suivi et paiement du transport public</Text>
            </View>
            <TextInput
                style={styles.input}
                value={email}
                onChangeText={setEmail}
                placeholder="Email"
                keyboardType="email-address"
                autoCapitalize="none"
            />
            <TextInput
                style={styles.input}
                value={password}
                onChangeText={setPassword}
                placeholder="Mot de passe"
                secureTextEntry
            />
            <TouchableOpacity style={styles.button} onPress={handleLogin}>
                <Text style={styles.buttonText}>Se Connecter</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.link} onPress={() => navigation.navigate('Signup')}>
                <Text style={styles.linkText}>Pas de compte ? Créer un compte</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: '#f5f6fa' },
    brand: { alignItems: 'center', marginBottom: 34 },
    appName: { fontSize: 38, fontWeight: 'bold', textAlign: 'center', marginTop: 12, color: '#2f3640', letterSpacing: 2 },
    subtitle: { fontSize: 15, textAlign: 'center', marginTop: 6, color: '#718093' },
    input: { backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 15, fontSize: 16 },
    button: { backgroundColor: '#00a8ff', padding: 15, borderRadius: 10, alignItems: 'center' },
    buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
    link: { marginTop: 20, alignItems: 'center' },
    linkText: { color: '#00a8ff', fontSize: 16 }
});

export default LoginScreen;
