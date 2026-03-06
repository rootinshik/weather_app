/*
  # Create saved cities table for WEAtrack
  
  1. New Tables
    - `saved_cities`
      - `id` (uuid, primary key) - Unique identifier
      - `city_name` (text) - Name of the city
      - `latitude` (numeric) - City latitude for weather API
      - `longitude` (numeric) - City longitude for weather API
      - `country` (text) - Country name
      - `state` (text, nullable) - State/region name
      - `created_at` (timestamptz) - When city was saved
      - `order_index` (integer) - Display order for cities
  
  2. Security
    - Enable RLS on `saved_cities` table
    - Public read access for demonstration purposes
    - Public write access for demonstration purposes (no auth required for this demo)
*/

CREATE TABLE IF NOT EXISTS saved_cities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  city_name text NOT NULL,
  latitude numeric NOT NULL,
  longitude numeric NOT NULL,
  country text NOT NULL,
  state text,
  order_index integer DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE saved_cities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view saved cities"
  ON saved_cities
  FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Anyone can insert cities"
  ON saved_cities
  FOR INSERT
  TO anon
  WITH CHECK (true);

CREATE POLICY "Anyone can delete cities"
  ON saved_cities
  FOR DELETE
  TO anon
  USING (true);

CREATE POLICY "Anyone can update cities"
  ON saved_cities
  FOR UPDATE
  TO anon
  USING (true)
  WITH CHECK (true);