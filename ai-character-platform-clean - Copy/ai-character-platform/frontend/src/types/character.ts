export interface Character {
  id: string;
  name: string;
  age: number;
  nationality: string;
  occupation: string;
  category: string;
  personality: string[];
  hobbies: string[];
  interests: string[];
  communication_style: string;
  interaction_style: string;
  emotional_traits: string[];
  description: string;
  backstory: string;
  greeting: string;
  system_prompt: string;
  avatar_prompt: string;
  avatar_url: string;
  created_at: string;
}

export interface CharacterListResponse {
  characters: Character[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface GenerateRequest {
  category?: string;
  nationality?: string;
  count: number;
}

export interface StatsResponse {
  total_characters: number;
  by_category: Record<string, number>;
}

export const CATEGORIES = [
  "College Student", "Doctor", "Teacher", "Entrepreneur",
  "Software Engineer", "Fitness Trainer", "Artist", "Gamer",
  "Travel Blogger", "Fashion Designer", "Influencer", "Musician",
  "Photographer", "Writer", "Researcher", "Life Coach"
];

export const NATIONALITIES = [
  "Indian", "American", "British", "Japanese", "Brazilian",
  "French", "Korean", "Australian", "Canadian", "German",
  "Italian", "Spanish", "Chinese", "Mexican", "Nigerian",
  "South African", "Swedish", "Dutch", "Argentine", "Thai"
];
