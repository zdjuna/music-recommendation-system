#!/usr/bin/env python3
"""
Advanced Music Library Enricher
Uses the research-based emotion analyzer to provide sophisticated emotion analysis
"""

import pandas as pd
import logging
import time
from pathlib import Path
from research_based_emotion_analyzer import ResearchBasedEmotionAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_enricher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_existing_data():
    """Load existing enriched data"""
    data_file = Path("data/zdjuna_enriched.csv")
    
    if not data_file.exists():
        logger.error(f"Data file {data_file} not found!")
        return None
    
    try:
        df = pd.read_csv(data_file)
        logger.info(f"Loaded {len(df)} tracks from {data_file}")
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

def enrich_with_advanced_emotion_analysis(df, batch_size=50):
    """
    Enrich tracks with advanced emotion analysis
    """
    logger.info("Initializing Research-Based Emotion Analyzer...")
    analyzer = ResearchBasedEmotionAnalyzer()
    
    # Add new columns for advanced emotion analysis
    new_columns = [
        'advanced_emotion',
        'emotion_confidence', 
        'emotion_valence',
        'emotion_arousal',
        'emotion_dominance',
        'analysis_method',
        'emotion_probabilities'
    ]
    
    for col in new_columns:
        if col not in df.columns:
            df[col] = None
    
    # Process tracks in batches
    total_tracks = len(df)
    processed = 0
    
    for i in range(0, total_tracks, batch_size):
        batch_end = min(i + batch_size, total_tracks)
        batch = df.iloc[i:batch_end]
        
        logger.info(f"Processing batch {i//batch_size + 1}: tracks {i+1}-{batch_end} of {total_tracks}")
        
        for idx, row in batch.iterrows():
            try:
                # Prepare text for analysis
                lyrics = str(row.get('lyrics', '')) if pd.notna(row.get('lyrics')) else ''
                artist = str(row.get('artist', '')) if pd.notna(row.get('artist')) else ''
                title = str(row.get('title', '')) if pd.notna(row.get('title')) else ''
                
                # Skip if already processed with advanced analysis
                if pd.notna(row.get('advanced_emotion')) and row.get('analysis_method') in ['lexicon_sentiment', 'ml_enhanced']:
                    continue
                
                # Analyze emotion
                result = analyzer.analyze_emotion(lyrics, artist, title)
                
                # Update dataframe
                df.at[idx, 'advanced_emotion'] = result.primary_emotion
                df.at[idx, 'emotion_confidence'] = result.confidence
                df.at[idx, 'emotion_valence'] = result.valence
                df.at[idx, 'emotion_arousal'] = result.arousal
                df.at[idx, 'emotion_dominance'] = result.dominance
                df.at[idx, 'analysis_method'] = result.analysis_method
                df.at[idx, 'emotion_probabilities'] = str(result.emotion_probabilities)
                
                processed += 1
                
                # Log progress for interesting results
                if result.confidence > 0.7:
                    logger.info(f"  ✓ {artist} - {title}: {result.primary_emotion} "
                              f"(confidence: {result.confidence:.3f}, "
                              f"valence: {result.valence:.3f}, "
                              f"arousal: {result.arousal:.3f})")
                
            except Exception as e:
                logger.error(f"Error processing track {idx}: {e}")
                continue
        
        # Save progress every batch
        try:
            output_file = "data/zdjuna_advanced_enriched.csv"
            df.to_csv(output_file, index=False)
            logger.info(f"Saved progress to {output_file}")
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
        
        # Small delay to be respectful
        time.sleep(0.1)
    
    logger.info(f"Advanced emotion analysis completed! Processed {processed} tracks.")
    return df

def analyze_results(df):
    """Analyze and report on the enrichment results"""
    logger.info("\n" + "="*60)
    logger.info("ADVANCED EMOTION ANALYSIS RESULTS")
    logger.info("="*60)
    
    # Emotion distribution
    if 'advanced_emotion' in df.columns:
        emotion_counts = df['advanced_emotion'].value_counts()
        logger.info(f"\nEmotion Distribution:")
        for emotion, count in emotion_counts.items():
            percentage = (count / len(df)) * 100
            logger.info(f"  {emotion}: {count} tracks ({percentage:.1f}%)")
    
    # Confidence distribution
    if 'emotion_confidence' in df.columns:
        avg_confidence = df['emotion_confidence'].mean()
        high_confidence = (df['emotion_confidence'] > 0.7).sum()
        logger.info(f"\nConfidence Analysis:")
        logger.info(f"  Average confidence: {avg_confidence:.3f}")
        logger.info(f"  High confidence (>0.7): {high_confidence} tracks ({(high_confidence/len(df)*100):.1f}%)")
    
    # Valence/Arousal analysis
    if 'emotion_valence' in df.columns and 'emotion_arousal' in df.columns:
        avg_valence = df['emotion_valence'].mean()
        avg_arousal = df['emotion_arousal'].mean()
        
        positive_tracks = (df['emotion_valence'] > 0.3).sum()
        negative_tracks = (df['emotion_valence'] < -0.3).sum()
        high_energy = (df['emotion_arousal'] > 0.3).sum()
        low_energy = (df['emotion_arousal'] < -0.3).sum()
        
        logger.info(f"\nValence/Arousal Analysis:")
        logger.info(f"  Average valence: {avg_valence:.3f}")
        logger.info(f"  Average arousal: {avg_arousal:.3f}")
        logger.info(f"  Positive tracks (valence > 0.3): {positive_tracks} ({(positive_tracks/len(df)*100):.1f}%)")
        logger.info(f"  Negative tracks (valence < -0.3): {negative_tracks} ({(negative_tracks/len(df)*100):.1f}%)")
        logger.info(f"  High energy tracks (arousal > 0.3): {high_energy} ({(high_energy/len(df)*100):.1f}%)")
        logger.info(f"  Low energy tracks (arousal < -0.3): {low_energy} ({(low_energy/len(df)*100):.1f}%)")
    
    # Method distribution
    if 'analysis_method' in df.columns:
        method_counts = df['analysis_method'].value_counts()
        logger.info(f"\nAnalysis Method Distribution:")
        for method, count in method_counts.items():
            percentage = (count / len(df)) * 100
            logger.info(f"  {method}: {count} tracks ({percentage:.1f}%)")
    
    # Show some examples
    logger.info(f"\nExample High-Confidence Predictions:")
    high_conf_tracks = df[df['emotion_confidence'] > 0.8].head(10)
    for _, track in high_conf_tracks.iterrows():
        logger.info(f"  {track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}: "
                   f"{track.get('advanced_emotion', 'unknown')} "
                   f"(conf: {track.get('emotion_confidence', 0):.3f})")

def main():
    """Main execution function"""
    logger.info("Starting Advanced Music Library Enrichment")
    logger.info("Using Research-Based Emotion Analyzer")
    
    # Load existing data
    df = load_existing_data()
    if df is None:
        return
    
    logger.info(f"Starting with {len(df)} tracks")
    
    # Enrich with advanced emotion analysis
    df_enriched = enrich_with_advanced_emotion_analysis(df)
    
    # Save final results
    output_file = "data/zdjuna_advanced_enriched.csv"
    try:
        df_enriched.to_csv(output_file, index=False)
        logger.info(f"Final results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving final results: {e}")
        return
    
    # Analyze results
    analyze_results(df_enriched)
    
    logger.info("Advanced enrichment completed successfully!")

if __name__ == "__main__":
    main() 