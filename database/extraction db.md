Oui, c'est tout à fait possible et c'est une opération très courante avec PostgreSQL. L'outil standard pour réaliser cela est pg_dump.

pg_dump est un utilitaire en ligne de commande qui permet de créer une sauvegarde (un "dump") d'une base de données PostgreSQL. Il peut générer un script SQL contenant les instructions CREATE TABLE, CREATE INDEX, etc., nécessaires pour recréer la structure (le schéma) de la base de données, ainsi que les instructions INSERT ou COPY pour réinsérer les données.

Pour votre besoin, qui est d'extraire uniquement le schéma pour reconstituer la base de données "from scratch", vous utiliserez une option spécifique de pg_dump.

Étape 1 : Extraire le schéma de la base de données

La commande principale utilise l'option --schema-only (ou son alias -s).

Ouvrez un terminal ou une invite de commande et utilisez la commande suivante :

pg_dump --schema-only -U votre_utilisateur -d votre_base_de_donnees > schema_seul.sql


Détaillons cette commande :

pg_dump : L'exécutable de l'utilitaire.

--schema-only : C'est l'option clé. Elle indique à pg_dump de n'exporter que les définitions des objets (tables, vues, fonctions, séquences, index, etc.) et non les données.

-U votre_utilisateur : Spécifie le nom d'utilisateur PostgreSQL avec lequel se connecter.

-d votre_base_de_donnees : Spécifie le nom de la base de données que vous voulez exporter.

> schema_seul.sql : Ceci est une redirection standard de la sortie. Le script SQL généré sera écrit dans le fichier schema_seul.sql au lieu de s'afficher dans le terminal.

Options utiles supplémentaires :

Pour se connecter à un serveur distant :

-h nom_du_serveur : Pour spécifier l'hôte (ex: localhost ou une adresse IP).

-p numero_du_port : Pour spécifier le port (par défaut 5432).

Pour un script plus propre à la restauration :

--clean : Ajoute des commandes DROP ... avant chaque commande CREATE .... C'est très utile pour votre cas, car cela garantit que vous partez d'un état propre si vous exécutez le script sur une base qui pourrait déjà contenir des objets du même nom.

Exemple de commande complète et recommandée :

pg_dump -h localhost -p 5432 -U mon_user -d ma_db --schema-only --clean > mon_schema_complet.sql
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Après avoir exécuté cette commande, vous serez invité à saisir le mot de passe de l'utilisateur mon_user (sauf si vous avez configuré une autre méthode d'authentification). Le fichier mon_schema_complet.sql contiendra alors toutes les instructions SQL pour recréer la structure exacte de votre base de données.

Étape 2 : Reconstituer la base de données à partir du schéma

Maintenant que vous avez votre fichier mon_schema_complet.sql, vous pouvez l'utiliser pour créer une nouvelle base de données avec la même structure.

Créez une nouvelle base de données vide
Vous ne pouvez pas importer un schéma dans une base de données qui n'existe pas. Vous devez d'abord la créer. Vous pouvez le faire avec la commande createdb ou via une requête SQL (CREATE DATABASE ...).

Avec l'utilitaire createdb :

createdb -U votre_utilisateur nouvelle_base_de_donnees
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Importez le schéma avec psql
psql est le client interactif de PostgreSQL. Il peut exécuter un script SQL contenu dans un fichier grâce à l'option -f.

psql -U votre_utilisateur -d nouvelle_base_de_donnees -f mon_schema_complet.sql
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Détaillons cette commande :

psql : L'exécutable du client.

-U votre_utilisateur : L'utilisateur pour se connecter à la nouvelle base. Cet utilisateur doit avoir les droits pour créer des objets (tables, etc.).

-d nouvelle_base_de_donnees : Le nom de la base de données vide que vous venez de créer.

-f mon_schema_complet.sql : Le chemin vers votre fichier SQL contenant le schéma.

Une fois cette commande terminée, votre nouvelle_base_de_donnees aura exactement la même structure (tables, colonnes, types, contraintes, index, etc.) que votre base de données d'origine, mais elle sera complètement vide de données.

Résumé du processus complet (de A à Z)

Extraction du schéma :

pg_dump -U user_source -d db_source --schema-only --clean > schema.sql
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Création de la nouvelle base de données (sur la machine cible) :

createdb -U user_cible -O user_cible nouvelle_db
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

(L'option -O définit le propriétaire de la base, ce qui est une bonne pratique).

Restauration du schéma dans la nouvelle base :

psql -U user_cible -d nouvelle_db -f schema.sql
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

C'est la méthode standard, robuste et recommandée pour cloner la structure d'une base de données PostgreSQL.