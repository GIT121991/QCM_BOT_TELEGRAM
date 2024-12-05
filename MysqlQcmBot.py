import mysql.connector as MC


class DataBase:
    def __init__(self):
        # Configuration de la connexion à MySQL
        self.db_create = {
            'host': 'localhost',
            'user': 'root',
            'password': ''
        }
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'QcmBotDB'
        }

    def createDB(self):
        """
        Crée une base de données si elle n'existe pas encore.
        """
        # Connexion au serveur MySQL
        connexion = MC.connect(**self.db_create)
        cursor = connexion.cursor()

        # Commande SQL pour créer une base de données
        db_name = 'QcmBotDB'
        create_db_query = f"CREATE DATABASE IF NOT EXISTS {db_name}"
        cursor.execute(create_db_query)
        print("Base de données créée avec succès.")

        # Fermeture de la connexion
        cursor.close()
        connexion.close()

    def create_connection(self):
        """
        Crée une connexion à la base de données.
        """
        self.conn = MC.connect(**self.db_config)
        self.cursor = self.conn.cursor()

    def create_table_users(self):
        """
        Crée une table pour les utilisateurs (élèves).
        """
        self.create_connection()
        table_name = 'users'

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            score INT DEFAULT 0,
            current_question INT DEFAULT 0
        );
        """
        self.cursor.execute(create_table_query)
        print(f"Table '{table_name}' créée avec succès.")
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def create_table_themes(self):
        """
        Crée une table pour stocker les themes du QCM.
        """
        self.create_connection()
        table_name = 'themes'

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
        """
        self.cursor.execute(create_table_query)
        print(f"Table '{table_name}' créée avec succès.")
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

    def create_table_questions(self):
        """
        Crée une table pour stocker les questions du QCM.
        """
        self.create_connection()
        table_name = 'questions'

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            theme_id INT NOT NULL,
            question TEXT NOT NULL,
            option1 VARCHAR(255) NOT NULL,
            option2 VARCHAR(255) NOT NULL,
            option3 VARCHAR(255) NOT NULL,
            option4 VARCHAR(255) NOT NULL,
            correct_option VARCHAR(255) NOT NULL,
            FOREIGN KEY (theme_id) REFERENCES themes(id)
        );
        """
        try:
            self.cursor.execute(create_table_query)
            print(f"Table '{table_name}' créée avec succès.")
            self.conn.commit()
        except Exception as e:
            print(f"Erreur lors de la création de la table '{table_name}':", e)
        finally:
            self.cursor.close()
            self.conn.close()

    def create_table_scores_history(self):
        """
        Crée une table pour stocker l'historique des scores du QCM.
        """
        # Assurez-vous que la connexion est créée
        self.create_connection()
        table_name = 'scores_history'

        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                score INT NOT NULL,
                total_questions INT NOT NULL,
                attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            );
        """
        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print(f"Table '{table_name}' créée avec succès.")
        except Exception as e:
            print(f"Erreur lors de la création de la table '{table_name}': {e}")
        finally:
            self.cursor.close()
            self.conn.close()

    def insert_sample_questions(self):
        """
        Insère un thème et des questions d'exemple dans les tables `themes` et `questions`.
        """
        try:
            # Crée une connexion à la base de données
            self.create_connection()

            # Insérer un thème
            insert_theme_query = "INSERT INTO themes (name) VALUES (%s)"
            self.cursor.execute(insert_theme_query, ("Python Niveau 1",))

            # Récupérer l'ID du thème inséré
            theme_id = self.cursor.lastrowid

            # Insérer les questions liées au thème
            insert_questions_query = """
            INSERT INTO questions (theme_id, question, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            questions = [
                # 15 Questions existantes
                (theme_id, 'Quelle méthode permet d\'ajouter un élément à une liste en Python ?', 'append()', 'add()',
                 'insert()', 'extend()', 'append()'),
                (theme_id, 'Quel opérateur est utilisé pour la division entière en Python ?', '/', '%', '//', '**',
                 '//'),
                (theme_id, 'Comment commence un commentaire en Python ?', '#', '//', '<!--', '/*', '#'),
                (theme_id, 'Quelle est la commande pour afficher quelque chose en Python ?', 'print()', 'echo()',
                 'disp()', 'show()', 'print()'),
                (theme_id, 'Comment déclarer une variable en Python ?', 'var x = 5;', 'int x = 5;', 'x = 5',
                 'declare x = 5;', 'x = 5'),
                (theme_id, 'Quel type de données est utilisé pour une chaîne de caractères ?', 'string', 'char', 'str',
                 'texte', 'str'),
                (theme_id, 'Quel est le résultat de 10 % 3 en Python ?', '3', '1', '0', '10', '1'),
                (
                theme_id, 'Quelle est la méthode utilisée pour obtenir la longueur d\'une liste ?', 'length()', 'len()',
                'size()', 'count()', 'len()'),
                (theme_id, 'Quel mot-clé est utilisé pour créer une fonction ?', 'function', 'def', 'fun', 'method',
                 'def'),
                (theme_id, 'Quelle est la sortie de "print(2**3)" ?', '5', '6', '8', '9', '8'),
                (theme_id, 'Comment écrire une boucle qui s\'exécute 5 fois ?', 'for i in range(5):', 'while i <= 5:',
                 'do 5 times:', 'loop(5):', 'for i in range(5):'),
                (theme_id, 'Comment vérifier si une valeur est dans une liste ?', '"value" in liste',
                 '"value" exists liste', '"value" of liste', '"value" has liste', '"value" in liste'),
                (theme_id, 'Quel est le type de données d\'un nombre décimal en Python ?', 'int', 'float', 'decimal',
                 'double', 'float'),
                (theme_id, 'Quelle est la sortie de "print(type(5))" ?', 'float', 'integer', '<class \'int\'>',
                 '<class \'float\'>', '<class \'int\'>'),
                (theme_id, 'Quelle est la syntaxe correcte pour importer une bibliothèque ?', 'import bibliothèque',
                 'library bibliothèque', 'include bibliothèque', 'require bibliothèque', 'import bibliothèque'),

                # 5 Nouvelles questions
                (theme_id, 'Quelle méthode est utilisée pour supprimer un élément spécifique d\'une liste ?',
                 'remove()', 'delete()', 'pop()', 'clear()', 'remove()'),
                (theme_id, 'Quel mot-clé est utilisé pour gérer les exceptions en Python ?',
                 'try', 'catch', 'except', 'handle', 'try'),
                (theme_id, 'Quelle est la valeur par défaut d\'une variable non initialisée en Python ?',
                 'None', '0', 'undefined', 'null', 'None'),
                (theme_id, 'Quelle méthode est utilisée pour convertir une chaîne en majuscules ?',
                 'uppercase()', 'upper()', 'toUpper()', 'capitalize()', 'upper()'),
                (theme_id, 'Quel est le mot-clé utilisé pour arrêter une boucle prématurément ?',
                 'stop', 'end', 'break', 'exit', 'break')
            ]

            # Exécuter les insertions
            self.cursor.executemany(insert_questions_query, questions)
            self.conn.commit()

            print("Thème et questions insérés avec succès.")

        except Exception as e:
            print("Erreur lors de l'insertion des données :", e)

        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()

    def insert_theme1_questions(self):
        """
        Insère un thème et des questions d'exemple dans les tables `themes` et `questions`.
        """
        try:
            # Crée une connexion à la base de données
            self.create_connection()

            # Insérer un thème
            insert_theme_query = "INSERT INTO themes (name) VALUES (%s)"
            self.cursor.execute(insert_theme_query, ("Communication entre machines sur Internet (Vol 1)",))

            # Récupérer l'ID du thème inséré
            theme_id = self.cursor.lastrowid

            # Insérer les questions liées au thème
            insert_questions_query = """
            INSERT INTO questions (theme_id, question, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            questions = [
                # Questions extraites du document
                (theme_id, "Qu'est-ce que la communication entre machines ?",
                    "L'échange de données entre des appareils électroniques connectés.",
                    "La communication uniquement entre ordinateurs.",
                    "L'utilisation de téléphones pour discuter.",
                    "L'envoi de lettres par la poste.",
                    "L'échange de données entre des appareils électroniques connectés."),
                (theme_id, "Quel type de réseau permet une communication entre machines locales ?",
                    "WAN (Wide Area Network)", "LAN (Local Area Network)",
                    "VPN (Virtual Private Network)", "Internet",
                    "LAN (Local Area Network)"),
                (theme_id, "Quel est l'avantage principal d'un câble Ethernet ?",
                    "Mobilité", "Vitesse élevée", "Coût faible",
                    "Facilité d'installation", "Vitesse élevée"),
                (theme_id, "Quel est un inconvénient du Wi-Fi ?",
                    "Vitesse très élevée", "Mobilité limitée",
                    "Moins sécurisé si mal configuré",
                    "Coût d'installation élevé",
                    "Moins sécurisé si mal configuré"),
                (theme_id, "Quel moyen de communication utilise des signaux lumineux ?",
                    "Câble Ethernet", "Wi-Fi", "Fibre optique", "Bluetooth",
                    "Fibre optique"),
                (theme_id, "Quel est un avantage des réseaux cellulaires comme la 5G ?",
                    "Coût d'installation élevé", "Couverture géographique étendue",
                    "Latence élevée", "Débit limité", "Couverture géographique étendue"),
                (theme_id, "Quel type de communication est utilisé pour les zones éloignées ?",
                    "Communication par satellite", "Wi-Fi", "Bluetooth",
                    "Câble Ethernet", "Communication par satellite"),
                (theme_id, "Quel est le rôle d'un VPN ?",
                    "Augmenter la vitesse de connexion",
                    "Créer une connexion sécurisée",
                    "Remplacer le Wi-Fi",
                    "Transmettre des données par satellite",
                    "Créer une connexion sécurisée"),
                (theme_id, "Quel protocole assure le transfert fiable des données ?",
                    "UDP", "TCP/IP", "HTTP", "FTP", "TCP/IP"),
                (theme_id, "Quel est un inconvénient de la communication par satellite ?",
                    "Accès dans des zones difficiles", "Latence élevée",
                    "Vitesse très élevée", "Coût d'installation faible",
                    "Latence élevée"),
                (theme_id, "Quel type de communication est le plus courant dans un réseau local ?",
                    "Wi-Fi", "Bluetooth", "Câble Ethernet", "Fibre optique",
                    "Câble Ethernet"),
                (theme_id, "Quel est un avantage du Bluetooth ?",
                    "Vitesse très élevée", "Portée illimitée",
                    "Faible consommation d'énergie", "Coût d'installation faible",
                    "Faible consommation d'énergie"),
                (theme_id, "Quel protocole est utilisé pour sécuriser les échanges sur le web ?",
                    "FTP", "UDP", "HTTPS", "TCP", "HTTPS"),
                (theme_id, "Quel est un inconvénient de la technologie Powerline Communication (CPL) ?",
                    "Utilisation de l'infrastructure électrique existante",
                    "Performances variables selon la qualité du réseau électrique",
                    "Coût d'installation faible",
                    "Facilité d'utilisation",
                    "Performances variables selon la qualité du réseau électrique"),
                (theme_id, "Quel est l'impact de l'Internet des objets (IoT) ?",
                    "Il rend les appareils plus lents.",
                    "Il automatise et optimise divers aspects de la vie quotidienne.",
                    "Il limite la connectivité des appareils.",
                    "Il nécessite plus de câbles.",
                    "Il automatise et optimise divers aspects de la vie quotidienne."),
                # Questions supplémentaires créées
                (theme_id, "Quel est l'objectif principal du protocole DNS ?",
                    "Garantir la sécurité des données",
                    "Convertir les noms de domaine en adresses IP",
                    "Optimiser la vitesse des réseaux",
                    "Assurer la compatibilité entre les appareils",
                    "Convertir les noms de domaine en adresses IP"),
                (theme_id, "Quelle est la principale différence entre IPv4 et IPv6 ?",
                    "IPv4 est plus rapide que IPv6",
                    "IPv6 utilise un adressage 128 bits",
                    "IPv4 prend en charge la sécurité intégrée",
                    "IPv6 est incompatible avec le Wi-Fi",
                    "IPv6 utilise un adressage 128 bits"),
                (theme_id, "Quel appareil connecte des réseaux différents ?",
                    "Commutateur", "Routeur", "Point d'accès", "Hub",
                    "Routeur"),
                (theme_id, "Que fait une adresse MAC ?",
                    "Identifie un appareil sur un réseau local",
                    "Assure la sécurité des données",
                    "Gère le routage des paquets",
                    "Optimise la vitesse du Wi-Fi",
                    "Identifie un appareil sur un réseau local"),
                (theme_id, "Quel outil est souvent utilisé pour surveiller le trafic réseau ?",
                    "Wireshark", "Cisco", "Java", "DNS",
                    "Wireshark")
            ]

            self.cursor.executemany(insert_questions_query, questions)
            self.conn.commit()
            print("Thème et questions insérés avec succès.")

        except Exception as e:
            print("Erreur lors de l'insertion des questions :", e)
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()

    def insert_theme2_questions(self):
        """
        Insère un thème et des questions d'exemple dans les tables `themes` et `questions`.
        """
        try:
            # Crée une connexion à la base de données
            self.create_connection()

            # Insérer un thème
            insert_theme_query = "INSERT INTO themes (name) VALUES (%s)"
            self.cursor.execute(insert_theme_query, ("La structure des applications sur le réseau internet",))

            # Récupérer l'ID du thème inséré
            theme_id = self.cursor.lastrowid

            # Insérer les questions liées au thème
            insert_questions_query = """
            INSERT INTO questions (theme_id, question, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            questions = [
                # Questions extraites du document
                (theme_id, "Quel protocole est utilisé pour envoyer des emails ?",
                 "HTTP", "FTP", "SMTP", "DNS", "SMTP"),
                (theme_id, "Quel est le rôle principal d'un serveur dans une application réseau ?",
                 "Initier la communication", "Traiter les requêtes des clients",
                 "Stocker des fichiers", "Afficher des pages web",
                 "Traiter les requêtes des clients"),
                (theme_id,
                 "Quel protocole est utilisé pour la communication entre les navigateurs et les serveurs web ?",
                 "TCP", "HTTP", "SMTP", "IMAP", "HTTP"),
                (theme_id, "Dans une architecture client-serveur, qui demande des ressources ?",
                 "Le serveur", "Le client", "Le routeur", "Le protocole", "Le client"),
                (theme_id, "Quel protocole permet de traduire les noms de domaine en adresses IP ?",
                 "FTP", "DNS", "SMTP", "HTTP", "DNS"),
                (theme_id,
                 "Quel type d'architecture permet à chaque appareil d'agir à la fois comme client et serveur ?",
                 "Architecture client-serveur", "Architecture P2P",
                 "Architecture en nuage", "Architecture centralisée",
                 "Architecture P2P"),
                (theme_id, "Quel protocole est utilisé pour le transfert de fichiers entre des ordinateurs ?",
                 "SMTP", "FTP", "HTTP", "IMAP", "FTP"),
                (theme_id, "Quel est un des principaux défis des applications réseau ?",
                 "La couleur des pages", "La gestion de la montée en échelle",
                 "Le choix des polices", "La taille des images",
                 "La gestion de la montée en échelle"),
                (theme_id, "Quel protocole assure la transmission de données de manière fiable sur Internet ?",
                 "HTTP", "TCP/IP", "FTP", "SMTP", "TCP/IP"),
                (theme_id, "Quel type d'application utilise le protocole HTTP pour accéder aux informations ?",
                 "Applications de messagerie", "Applications Web",
                 "Services en temps réel", "Applications de bureau",
                 "Applications Web"),
                (theme_id, "Quel protocole est utilisé pour récupérer des emails depuis un serveur de messagerie ?",
                 "SMTP", "IMAP", "HTTP", "FTP", "IMAP"),
                (theme_id, "Quel est l'objectif principal d'un protocole de communication ?",
                 "Créer des images", "Régir la communication entre des appareils",
                 "Envoyer des messages texte", "Stocker des données",
                 "Régir la communication entre des appareils"),
                (theme_id, "Quel type d'application permet des communications audio et vidéo en temps réel ?",
                 "Applications de messagerie", "Applications Web",
                 "Services en temps réel", "Applications de bureau",
                 "Services en temps réel"),
                (theme_id, "Quel protocole gère l'envoi de messages électroniques ?",
                 "IMAP", "SMTP", "HTTP", "DNS", "SMTP"),
                (theme_id, "Quel est un avantage du modèle client-serveur ?",
                 "Décentralisation", "Facilité de gestion des données",
                 "Complexité accrue", "Moins de sécurité",
                 "Facilité de gestion des données"),
                # Questions supplémentaires
                (theme_id, "Quel protocole est utilisé pour télécharger des fichiers depuis un serveur ?",
                 "SMTP", "FTP", "DNS", "HTTP", "FTP"),
                (theme_id, "Quel est un inconvénient des architectures P2P ?",
                 "Gestion centralisée", "Dépendance à un serveur unique",
                 "Problèmes de sécurité et de montée en charge",
                 "Faible disponibilité",
                 "Problèmes de sécurité et de montée en charge"),
                (theme_id, "Quelle est la différence principale entre HTTP et HTTPS ?",
                 "HTTPS est plus rapide", "HTTPS utilise le chiffrement des données",
                 "HTTP est réservé aux emails", "HTTP et HTTPS sont identiques",
                 "HTTPS utilise le chiffrement des données"),
                (theme_id, "Quel type d'application utilise souvent le protocole UDP ?",
                 "Applications web", "Streaming audio et vidéo",
                 "Applications de messagerie", "Téléchargement de fichiers",
                 "Streaming audio et vidéo"),
                (theme_id, "Quel est un des rôles principaux du DNS ?",
                 "Créer des connexions sécurisées",
                 "Fournir des adresses IP pour les noms de domaine",
                 "Envoyer des emails",
                 "Optimiser les pages web",
                 "Fournir des adresses IP pour les noms de domaine")
            ]

            self.cursor.executemany(insert_questions_query, questions)
            self.conn.commit()
            print("Thème et questions insérés avec succès.")

        except Exception as e:
            print("Erreur lors de l'insertion des questions :", e)
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()

    def insert_theme3_questions(self):
        """
        Insère un thème et des questions d'exemple dans les tables `themes` et `questions`.
        """
        try:
            # Crée une connexion à la base de données
            self.create_connection()

            # Insérer un thème
            insert_theme_query = "INSERT INTO themes (name) VALUES (%s)"
            self.cursor.execute(insert_theme_query, ("Les Protocoles du Web",))

            # Récupérer l'ID du thème inséré
            theme_id = self.cursor.lastrowid

            # Insérer les questions liées au thème
            insert_questions_query = """
            INSERT INTO questions (theme_id, question, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            questions = [
                # Questions extraites du document
                (theme_id, "Quel protocole est utilisé pour sécuriser les échanges sur le web ?",
                 "FTP", "HTTP", "HTTPS", "DNS", "HTTPS"),
                (theme_id, "Quel est le rôle principal du protocole HTTP ?",
                 "Transférer des fichiers", "Afficher des pages web",
                 "Traduire des noms de domaine", "Chiffrer les données",
                 "Afficher des pages web"),
                (theme_id, "Quel protocole est utilisé pour le transfert de fichiers entre un client et un serveur ?",
                 "HTTP", "FTP", "HTTPS", "DNS", "FTP"),
                (theme_id, "Quel est l'objectif principal du DNS ?",
                 "Chiffrer les données", "Traduire les noms de domaine en adresses IP",
                 "Transférer des fichiers", "Afficher des pages web",
                 "Traduire les noms de domaine en adresses IP"),
                (theme_id, "Quel protocole assure la confidentialité des données échangées sur le web ?",
                 "HTTP", "FTP", "HTTPS", "TCP", "HTTPS"),
                (theme_id, "Quel type de serveur est responsable de l'hébergement des pages web ?",
                 "Serveur de fichiers", "Serveur de messagerie",
                 "Serveur web", "Serveur DNS", "Serveur web"),
                (theme_id, "Quel protocole est principalement utilisé pour naviguer sur le web ?",
                 "FTP", "HTTP", "SMTP", "SNMP", "HTTP"),
                (theme_id, "Quel protocole permet de télécharger des fichiers depuis un serveur ?",
                 "HTTP", "FTP", "HTTPS", "DNS", "FTP"),
                (theme_id, "Quel est un avantage de l'utilisation de HTTPS par rapport à HTTP ?",
                 "Il est plus rapide", "Il est plus facile à utiliser",
                 "Il est plus sécurisé", "Il consomme moins de données",
                 "Il est plus sécurisé"),
                (theme_id, "Quel type de serveur traduit les noms de domaine en adresses IP ?",
                 "Serveur web", "Serveur FTP", "Serveur DNS", "Serveur de fichiers",
                 "Serveur DNS"),
                (theme_id, "Quel protocole est utilisé pour envoyer des emails ?",
                 "FTP", "HTTP", "SMTP", "HTTPS", "SMTP"),
                (theme_id,
                 "Quel protocole est souvent utilisé pour le transfert de fichiers dans un environnement sécurisé ?",
                 "HTTP", "FTP", "SFTP", "DNS", "SFTP"),
                (theme_id, "Quel protocole est essentiel pour le chargement des pages web ?",
                 "FTP", "HTTP", "DNS", "SNMP", "HTTP"),
                (theme_id, "Quel est le principal inconvénient de l'utilisation de FTP ?",
                 "Il est trop lent", "Il n'est pas sécurisé",
                 "Il ne permet pas le transfert de fichiers", "Il est trop compliqué",
                 "Il n'est pas sécurisé"),
                (theme_id, "Quel protocole est utilisé pour sécuriser les transactions en ligne ?",
                 "HTTP", "FTP", "HTTPS", "DNS", "HTTPS"),
                # Questions supplémentaires
                (theme_id, "Quel protocole est utilisé pour synchroniser les emails sur plusieurs appareils ?",
                 "SMTP", "IMAP", "POP3", "DNS", "IMAP"),
                (theme_id, "Quel est le rôle principal du protocole TCP ?",
                 "Gérer les connexions fiables", "Transférer des fichiers",
                 "Fournir un chiffrement", "Optimiser les pages web",
                 "Gérer les connexions fiables"),
                (theme_id, "Quel protocole est utilisé pour partager des fichiers dans un réseau local ?",
                 "FTP", "SMB", "HTTP", "DNS", "SMB"),
                (theme_id, "Quel est l'avantage principal de l'utilisation de DNS ?",
                 "Augmenter la vitesse de connexion", "Simplifier l'accès aux sites web via des noms de domaine",
                 "Assurer la sécurité des données", "Réduire la latence",
                 "Simplifier l'accès aux sites web via des noms de domaine"),
                (theme_id, "Quel protocole est utilisé pour la gestion des appareils réseau ?",
                 "FTP", "SNMP", "HTTP", "TCP", "SNMP")
            ]

            self.cursor.executemany(insert_questions_query, questions)
            self.conn.commit()
            print("Thème et questions insérés avec succès.")

        except Exception as e:
            print("Erreur lors de l'insertion des questions :", e)
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()

    def insert_theme4_questions(self):
        """
        Insère un thème et des questions d'exemple dans les tables `themes` et `questions`.
        """
        try:
            # Crée une connexion à la base de données
            self.create_connection()

            # Insérer un thème
            insert_theme_query = "INSERT INTO themes (name) VALUES (%s)"
            self.cursor.execute(insert_theme_query, ("Quiz sur les Moteurs de Recherche",))

            # Récupérer l'ID du thème inséré
            theme_id = self.cursor.lastrowid

            # Insérer les questions liées au thème
            insert_questions_query = """
            INSERT INTO questions (theme_id, question, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            questions = [
                # Questions fournies
                (theme_id, "Quel est le rôle principal d'un moteur de recherche ?",
                 "Créer des sites web", "Répondre à des requêtes en fournissant des résultats pertinents",
                 "Envoyer des emails", "Télécharger des fichiers",
                 "Répondre à des requêtes en fournissant des résultats pertinents"),
                (theme_id, "Comment les moteurs de recherche collectent-ils des informations sur les pages web ?",
                 "En demandant aux utilisateurs", "En utilisant des robots appelés crawlers",
                 "En lisant les livres", "En regardant des vidéos",
                 "En utilisant des robots appelés crawlers"),
                (theme_id,
                 "Quel est le terme utilisé pour décrire l'optimisation des sites web afin d'améliorer leur classement dans les résultats de recherche ?",
                 "SEO (Search Engine Optimization)", "HTML",
                 "URL", "CSS",
                 "SEO (Search Engine Optimization)"),
                (theme_id, "Quel algorithme est utilisé pour classer les résultats de recherche ?",
                 "Algorithme de tri", "Algorithme de classement",
                 "Algorithme de recherche", "Algorithme de calcul",
                 "Algorithme de classement"),
                (theme_id,
                 "Quel moteur de recherche est connu pour sa protection de la vie privée et ne collecte pas de données personnelles ?",
                 "Google", "Bing", "DuckDuckGo", "Yahoo!",
                 "DuckDuckGo"),
                (theme_id, "Quel moteur de recherche est principalement utilisé en Chine ?",
                 "Google", "Baidu", "Yahoo!", "Ecosia",
                 "Baidu"),
                (theme_id, "Quel type de moteur de recherche est Qwant ?",
                 "Moteur de recherche axé sur la vitesse",
                 "Moteur de recherche respectueux de la vie privée",
                 "Moteur de recherche pour les enfants",
                 "Moteur de recherche pour les images",
                 "Moteur de recherche respectueux de la vie privée"),
                (theme_id, "Quel est l'impact de l'intelligence artificielle sur les moteurs de recherche ?",
                 "Elle rend les moteurs de recherche plus lents",
                 "Elle améliore la précision et la personnalisation des résultats",
                 "Elle supprime les résultats de recherche",
                 "Elle ne change rien",
                 "Elle améliore la précision et la personnalisation des résultats"),
                (theme_id,
                 "Quel navigateur est connu pour sa personnalisation avancée et son respect de la vie privée ?",
                 "Google Chrome", "Mozilla Firefox", "Microsoft Edge", "Safari",
                 "Mozilla Firefox"),
                (theme_id, "Quel moteur de recherche est le plus populaire au monde ?",
                 "Bing", "Yahoo!", "Google", "DuckDuckGo",
                 "Google"),
                (theme_id, "Quel est le rôle des mots-clés dans le référencement ?",
                 "Ils n'ont pas d'importance",
                 "Ils aident à trouver des informations",
                 "Ils ralentissent la recherche",
                 "Ils sont utilisés pour créer des images",
                 "Ils aident à trouver des informations"),
                (theme_id, "Quel navigateur est le successeur d'Internet Explorer ?",
                 "Opera", "Microsoft Edge", "Brave", "Vivaldi",
                 "Microsoft Edge"),
                (theme_id, "Quel moteur de recherche plante des arbres à chaque recherche effectuée ?",
                 "Google", "Ecosia", "Yandex", "Baidu",
                 "Ecosia"),
                (theme_id,
                 "Quel type de recherche a été intégré par les moteurs de recherche modernes pour faciliter l'accès à l'information ?",
                 "Recherche manuelle", "Recherche vocale et visuelle",
                 "Recherche par email", "Recherche par courrier",
                 "Recherche vocale et visuelle"),
                (theme_id,
                 "Quel est un des enjeux majeurs des moteurs de recherche concernant les données des utilisateurs ?",
                 "Augmenter la vitesse de recherche",
                 "Protection de la vie privée",
                 "Améliorer l'esthétique des sites",
                 "Réduire le nombre de résultats",
                 "Protection de la vie privée"),
                # Questions supplémentaires
                (theme_id, "Quel moteur de recherche est connu pour utiliser des énergies renouvelables ?",
                 "Google", "Bing", "Ecosia", "Yahoo!",
                 "Ecosia"),
                (theme_id, "Quel est un exemple de recherche avancée ?",
                 "Utiliser des opérateurs comme \"site:\" ou \"intitle:\"",
                 "Naviguer sur les réseaux sociaux",
                 "Regarder des vidéos",
                 "Envoyer des emails",
                 "Utiliser des opérateurs comme \"site:\" ou \"intitle:\""),
                (theme_id, "Quel est l'objectif principal des crawlers ?",
                 "Indexer les pages web", "Supprimer les pages obsolètes",
                 "Classer les mots-clés", "Optimiser les résultats",
                 "Indexer les pages web"),
                (theme_id, "Quel moteur de recherche russe est populaire en Russie ?",
                 "Google", "Yandex", "Bing", "DuckDuckGo",
                 "Yandex"),
                (theme_id, "Quel est le rôle d'un sitemap dans le référencement ?",
                 "Réduire la vitesse du site",
                 "Faciliter l'exploration des pages par les moteurs de recherche",
                 "Augmenter les publicités",
                 "Améliorer les couleurs du site",
                 "Faciliter l'exploration des pages par les moteurs de recherche")
            ]

            self.cursor.executemany(insert_questions_query, questions)
            self.conn.commit()
            print("Thème et questions insérés avec succès.")

        except Exception as e:
            print("Erreur lors de l'insertion des questions :", e)
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()


# Initialisation et création de la base de données
db = DataBase()
db.createDB()
db.create_table_users()
db.create_table_themes()
db.create_table_questions()
db.insert_sample_questions()
db.insert_theme1_questions()
db.insert_theme2_questions()
db.insert_theme3_questions()
db.insert_theme4_questions()
db.create_table_scores_history()
