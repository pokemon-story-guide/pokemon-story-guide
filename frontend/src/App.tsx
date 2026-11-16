import { Navigate, Route, Routes } from "react-router-dom";
import { MENU_ITEMS } from "./config/menuItems";
import { MainMenuPage } from "./pages/MainMenuPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ChampionPage } from "./pages/trainers/ChampionPage";
import { EliteFourPage } from "./pages/trainers/EliteFourPage";
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
      {/* 맵 정보, 포켓몬 정보는 아직 자리표시자입니다. */}
      {MENU_ITEMS.filter((item) => item.id !== "trainers").map((item) => (
        <Route key={item.id} path={item.path} element={<PlaceholderPage title={item.label} />} />
      ))}

      <Route path="/trainers" element={<TrainerCategoryPage />} />
      <Route path="/trainers/gym" element={<GymSelectPage />} />
      <Route path="/trainers/elite" element={<EliteSelectPage />} />
      <Route path="/trainers/elite/four" element={<EliteFourPage />} />
      <Route path="/trainers/elite/champion" element={<ChampionPage />} />
      <Route path="/trainers/plasma" element={<PlasmaSelectPage />} />
      <Route path="/trainers/plasma/n" element={<NStoryPage />} />
      <Route path="/trainers/detail/:trainerId" element={<TrainerDetailPage />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
