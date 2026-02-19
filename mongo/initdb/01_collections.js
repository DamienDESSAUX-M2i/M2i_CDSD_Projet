db = db.getSiblingDB('admin');

// ===
// Data Base
// ===

db = db.getSiblingDB('audio_midi');

// ===
// Collections
// ===

db.createCollection('beat_position', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['title', 'dataset_name', 'beat_position'],
            properties: {
                title: { 
                    bsonType: 'string',
                    description: "Titre obligatoire et doit être une string"
                },
                dataset_name: { 
                    bsonType: 'string',
                    description: "Nom du dataset obligatoire et doit être une string"
                },
                beat_position: {
                    bsonType: 'array',
                    description: "Liste des objets de position de beat",
                    items: {
                        bsonType: 'object',
                        required: ['time', 'position', 'beat_units', 'measure', 'num_beats'],
                        properties: {
                            time: {
                                bsonType: 'double',
                                description: "Temps (float/double) obligatoire"
                            },
                            position: {
                                bsonType: 'int',
                                description: "Position (entier) obligatoire"
                            },
                            beat_units: {
                                bsonType: 'int',
                                description: "Unités de beat (entier) obligatoire"
                            },
                            measure: {
                                bsonType: 'int',
                                description: "Mesure (entier) obligatoire"
                            },
                            num_beats: {
                                bsonType: 'int',
                                description: "Nombre de beats (entier) obligatoire"
                            }
                        }
                    }
                },
                inserted_at: {
                    bsonType: 'date',
                    description: "Date d'insertion"
                }
            }
        }
    },
    validationLevel: 'moderate'
});

db.createCollection('chord', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['title', 'dataset_name', 'chord'],
            properties: {
                title: { 
                    bsonType: 'string',
                    description: "Titre obligatoire et doit être une string"
                },
                dataset_name: { 
                    bsonType: 'string',
                    description: "Nom du dataset obligatoire et doit être une string"
                },
                chord: {
                    bsonType: 'array',
                    description: "Liste des objets accords",
                    items: {
                        bsonType: 'object',
                        required: ['time', 'duration', 'value'],
                        properties: {
                            time: {
                                bsonType: 'double',
                                description: "Temps du début (float)"
                            },
                            duration: {
                                bsonType: 'double',
                                description: "Durée (float)"
                            },
                            value: {
                                bsonType: 'string',
                                description: "Nom ou valeur de l'accord (string)"
                            }
                        }
                    }
                },
                inserted_at: {
                    bsonType: 'date',
                    description: "Date d'insertion"
                }
            }
        }
    },
    validationLevel: 'moderate'
});

db.createCollection('note_midi', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['title', 'dataset_name'],
            properties: {
                title: { 
                    bsonType: 'string',
                    description: "Titre obligatoire et doit être une string"
                },
                dataset_name: { 
                    bsonType: 'string',
                    description: "Nom du dataset obligatoire et doit être une string"
                },
                note_midi: {
                    bsonType: 'array',
                    description: "Liste des objets contenant les données sources MIDI",
                    items: {
                        bsonType: 'object',
                        required: ['data_source', 'time', 'duration', 'value'],
                        properties: {
                            data_source: { bsonType: 'string' },
                            time: { bsonType: 'double' },
                            duration: { bsonType: 'double' },
                            value: { bsonType: 'double' }
                        }
                    }
                },
                transcription: {
                    bsonType: 'array',
                    description: "Liste des objets contenant les détails de la transcription",
                    items: {
                        bsonType: 'object',
                        properties: {
                            pitch: { bsonType: ['int', 'null'] },
                            onset: { bsonType: ['double', 'null'] },
                            offset: { bsonType: ['double', 'null'] },
                            fret_number: { bsonType: ['int', 'null'] },
                            string_number: { bsonType: ['int', 'null'] },
                            excitation_style: { bsonType: ['string', 'null'] },
                            expression_style: { bsonType: ['string', 'null'] },
                            loudness: { bsonType: ['string', 'null'] },
                            modulation_frequency_range: { bsonType: ['double', 'null'] },
                            modulation_frequency: { bsonType: ['double', 'null'] }
                        }
                    }
                },
                inserted_at: {
                    bsonType: 'date',
                    description: "Date d'insertion"
                }
            }
        }
    },
    validationLevel: 'moderate'
});

db.createCollection('pitch_contour', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['title', 'dataset_name', 'pitch_contour'],
            properties: {
                title: { 
                    bsonType: 'string',
                    description: "Titre obligatoire (string)"
                },
                dataset_name: { 
                    bsonType: 'string',
                    description: "Nom du dataset obligatoire (string)"
                },
                pitch_contour: {
                    bsonType: 'array',
                    description: "Liste des objets contenant les données du contour mélodique",
                    items: {
                        bsonType: 'object',
                        required: ['data_source', 'time', 'frequency'],
                        properties: {
                            data_source: {
                                bsonType: 'string',
                                description: "Source des données (ex: nom de l'algorithme)"
                            },
                            time: {
                                bsonType: 'double',
                                description: "Timestamp unique (float/double)"
                            },
                            frequency: {
                                bsonType: 'double',
                                description: "Fréquence en Hz (float/double)"
                            }
                        }
                    }
                },
                inserted_at: {
                    bsonType: 'date',
                    description: "Date d'insertion"
                }
            }
        }
    },
    validationLevel: 'moderate'
});

// ===
// Indexes
// ===

db.beat_position.createIndex(
    { title: 1, dataset_name: 1 },
    { unique: true, name: "unique_title_dataset" }
);

db.chord.createIndex(
    { title: 1, dataset_name: 1 },
    { unique: true, name: "unique_title_dataset" }
);

db.note_midi.createIndex(
    { title: 1, dataset_name: 1 },
    { unique: true, name: "unique_title_dataset" }
);

db.pitch_contour.createIndex(
    { title: 1, dataset_name: 1 },
    { unique: true, name: "unique_title_dataset" }
);
