import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator, ScrollView } from 'react-native';
import axios from 'axios';

const roleOptions = [
    { label: 'Passager', value: 'PASSENGER' },
    { label: 'Conducteur', value: 'DRIVER' },
    { label: 'Controleur', value: 'CONTROLLER' },
    { label: 'Administrateur', value: 'ADMIN' },
];

const SignupScreen = ({ navigation }) => {
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('+216');
    const [role, setRole] = useState('PASSENGER');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSignup = async () => {
        if (!firstName || !lastName || !email || !phone || !role || !password || !confirmPassword) {
            Alert.alert("Erreur", "Tous les champs sont obligatoires");
            return;
        }
        if (password !== confirmPassword) {
            Alert.alert("Erreur", "Les mots de passe ne correspondent pas");
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/auth/register/`, {
                first_name: firstName.trim(),
                last_name: lastName.trim(),
                email: email.trim().toLowerCase(),
                phone_number: phone,
                password: password,
                role: role
            });

            Alert.alert("Succès", "Compte créé ! Vous pouvez maintenant vous connecter.");
            navigation.navigate('Login');
        } catch (error) {
            const errorMsg = error.response?.data?.error || "Une erreur est survenue lors de l'inscription";
            Alert.alert("Erreur", errorMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
            <Text style={styles.title}>Créer un Compte</Text>
            <Text style={styles.subtitle}>Completez vos informations pour rejoindre SITP.</Text>
            
            <TextInput
                style={styles.input}
                value={firstName}
                onChangeText={setFirstName}
                placeholder="Prénom"
                autoCapitalize="words"
            />

            <TextInput
                style={styles.input}
                value={lastName}
                onChangeText={setLastName}
                placeholder="Nom"
                autoCapitalize="words"
            />

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
                value={phone}
                onChangeText={setPhone}
                placeholder="Numéro de Téléphone"
                keyboardType="phone-pad"
            />
            
            <Text style={styles.sectionLabel}>Choisir votre rôle</Text>
            <View style={styles.roleGrid}>
                {roleOptions.map((option) => (
                    <TouchableOpacity
                        key={option.value}
                        style={[styles.roleButton, role === option.value && styles.roleButtonActive]}
                        onPress={() => setRole(option.value)}
                    >
                        <Text style={[styles.roleText, role === option.value && styles.roleTextActive]}>{option.label}</Text>
                    </TouchableOpacity>
                ))}
            </View>
            
            <TextInput
                style={styles.input}
                value={password}
                onChangeText={setPassword}
                placeholder="Mot de passe"
                secureTextEntry
            />

            <TextInput
                style={styles.input}
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                placeholder="Confirmer le mot de passe"
                secureTextEntry
            />

            <TouchableOpacity style={styles.button} onPress={handleSignup} disabled={loading}>
                {loading ? (
                    <ActivityIndicator color="#fff" />
                ) : (
                    <Text style={styles.buttonText}>S'inscrire</Text>
                )}
            </TouchableOpacity>

            <TouchableOpacity style={styles.link} onPress={() => navigation.navigate('Login')}>
                <Text style={styles.linkText}>Déjà un compte ? Se connecter</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flexGrow: 1, justifyContent: 'center', padding: 20, backgroundColor: '#f5f6fa' },
    title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 8, color: '#2f3640' },
    subtitle: { fontSize: 15, textAlign: 'center', marginBottom: 28, color: '#718093' },
    input: { backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 15, fontSize: 16 },
    sectionLabel: { fontSize: 15, fontWeight: '700', color: '#2f3640', marginBottom: 10 },
    roleGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 15 },
    roleButton: { width: '48%', backgroundColor: '#fff', borderRadius: 10, padding: 13, borderWidth: 1, borderColor: '#dcdde1', alignItems: 'center' },
    roleButtonActive: { backgroundColor: '#00a8ff', borderColor: '#00a8ff' },
    roleText: { color: '#2f3640', fontWeight: '700' },
    roleTextActive: { color: '#fff' },
    button: { backgroundColor: '#4cd137', padding: 15, borderRadius: 10, alignItems: 'center', marginTop: 10 },
    buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
    link: { marginTop: 20, alignItems: 'center' },
    linkText: { color: '#00a8ff', fontSize: 16 }
});

export default SignupScreen;
