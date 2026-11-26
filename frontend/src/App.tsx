import { Navigate, Route, Routes } from "react-router-dom";
import { MainMenuPage } from "./pages/MainMenuPage";
import { MapInfoPage } from "./pages/MapInfoPage";
import { PokemonDetailPage } from "./pages/PokemonDetailPage";
import { PokemonSearchPage } from "./pages/PokemonSearchPage";
import { EliteSelectPage } from "./pages/trainers/EliteSelectPage";
import { GymSelectPage } from "./pages/trainers/GymSelectPage";
import { NStoryPage } from "./pages/trainers/NStoryPage";
import { PlasmaSelectPage } from "./pages/trainers/PlasmaSelectPage";
import { TrainerCategoryPage } from "./pages/trainers/TrainerCategoryPage";
import { TrainerDetailPage } from "./pages/trainers/TrainerDetailPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<MainMenuPage />} />
      <Route path="/map" element={<MapInfoPage />} />

      <Route path="/pokemon" element={<PokemonSearchPage />} />
      <Route path="/pokemon/:pokemonId" element={<PokemonDetailPage />} />

      <Route path="/trainers" element={<TrainerCategoryPage />} />
      <Route path="/trainers/gym" element={<GymSelectPage />} />
      <Route path="/trainers/elite" element={<EliteSelectPage />} />
      <Route path="/trainers/plasma" element={<PlasmaSelectPage />} />
      <Route path="/trainers/plasma/n" element={<NStoryPage />} />
      <Route path="/trainers/detail/:trainerId" element={<TrainerDetailPage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
