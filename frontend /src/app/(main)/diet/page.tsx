"use client";

import { useState, useEffect } from "react";
import { Instrument_Serif } from "next/font/google";

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument",
  subsets: ["latin"],
  weight: ["400"],
  style: ["italic"],
});

// Define TypeScript interfaces for our data structure
interface Ingredient {
  name?: string;
  ingredients?: string[];
  calories?: number;
}

interface Meal {
  mealType?: string;
  items?: Ingredient[];
}

interface DayPlan {
  day?: string;
  totalCalories?: number;
  macronutrients?: {
    carbohydrates?: number;
    proteins?: number;
    fats?: number;
  };
  meals?: Meal[];
}

interface WorkoutDay {
  day?: string;
  routine?: string;
}

interface CalorieDistribution {
  category?: string;
  percentage?: string;
}

interface DietData {
  dailyNutrition?: {
    calories?: number;
    carbs?: number;
    fats?: number;
    protein?: number;
    waterIntake?: string;
  };
  calorieDistribution?: CalorieDistribution[];
  goal?: string;
  dietPreference?: string;
  workoutRoutine?: WorkoutDay[];
  mealPlans?: DayPlan[];
}

interface FetchedDietItem {
  _id?: string;
  diet_plan?: DietData;
}

// Tab Button Component
const TabButton = ({ children, active, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`px-6 py-3 rounded-lg transition-all duration-300 font-medium text-lg ${
        active
          ? "bg-purple-800 text-white shadow-lg shadow-purple-900/50"
          : "bg-gray-800 text-purple-300 hover:bg-gray-700"
      }`}
    >
      {children}
    </button>
  );
};

// Diet Card Component
const DietCard = ({ diet, onClick, index }) => {
  // Generate a suitable title based on available properties
  const generateTitle = () => {
    return ` Diet #${index + 1}`;
  };

  return (
    <div
      onClick={onClick}
      className="bg-gray-800 rounded-xl overflow-hidden shadow-lg border border-purple-800/50 cursor-pointer transform transition-all duration-300 hover:scale-105 hover:shadow-xl hover:border-purple-600"
    >
      <div className="bg-purple-900 p-4">
        <h3 className="text-2xl font-semibold text-white">{generateTitle()}</h3>
        <div className="text-sm mt-2 text-purple-200 capitalize">{diet?.goal || "Custom Plan"}</div>
      </div>
      <div className="p-6">
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm mb-4">
          <span>Calories: <strong>{diet?.dailyNutrition?.calories} kcal</strong></span>
          <span>Protein: <strong>{diet?.dailyNutrition?.protein}g</strong></span>
        </div>
        <div className="text-purple-300 text-sm capitalize">
          {diet?.dietPreference || "Custom"} diet • {diet?.mealPlans?.length} day plan
        </div>
      </div>
    </div>
  );
};

export default function Page() {
  const [dietsList, setDietsList] = useState<DietData[]>([]);
  const [selectedDiet, setSelectedDiet] = useState<DietData | null>(null);
  const [activeTab, setActiveTab] = useState<string>("plans");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDiets = async () => {
      try {
        setLoading(true);
        const response = await fetch("http://localhost:8000/diets");
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();

        console.log("Fetched diets raw:", data);

        // Map the fetched data to extract diet_plan, using optional chaining
        const extractedDiets: DietData[] = data.map(item => ({
          dailyNutrition: {
            calories: item?.AI_Plan?.diet_plan?.dailyNutrition?.calories,
            carbs: item?.AI_Plan?.diet_plan?.dailyNutrition?.carbs,
            fats: item?.AI_Plan?.diet_plan?.dailyNutrition?.fats,
            protein: item?.AI_Plan?.diet_plan?.dailyNutrition?.protein,
            waterIntake: item?.AI_Plan?.diet_plan?.dailyNutrition?.waterIntake,
          },
          calorieDistribution: item?.AI_Plan?.diet_plan?.calorieDistribution?.map(dist => ({
            category: dist?.category,
            percentage: dist?.percentage,
          })),
          goal: item?.AI_Plan?.diet_plan?.goal,
          dietPreference: item?.AI_Plan?.diet_plan?.dietPreference,
          workoutRoutine: item?.AI_Plan?.diet_plan?.workoutRoutine?.map(workout => ({
            day: workout?.day,
            routine: workout?.routine,
          })),
          mealPlans: item?.AI_Plan?.diet_plan?.mealPlans?.map(plan => ({
            day: plan?.day,
            totalCalories: plan?.totalCalories,
            macronutrients: {
              carbohydrates: plan?.macronutrients?.carbohydrates,
              proteins: plan?.macronutrients?.proteins,
              fats: plan?.macronutrients?.fats,
            },
            meals: plan?.meals?.map(meal => ({
              mealType: meal?.mealType,
              items: meal?.items?.map(ing => ({
                name: ing?.name,
                ingredients: ing?.ingredients,
                calories: ing?.calories,
              })),
            })),
          })),
        }));

        console.log("Extracted diets:", extractedDiets);
        setDietsList(extractedDiets);
        setLoading(false);
      } catch (err: any) {
        console.error("Fetch error:", err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchDiets();
  }, []);

  const handleDietSelect = (diet: DietData) => {
    setSelectedDiet(diet);
    setActiveTab("overview");
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToList = () => {
    setSelectedDiet(null);
  };

  // Generate title for selected diet
  const getSelectedDietTitle = () => {
    if (!selectedDiet) return "";
    const prefix = selectedDiet.dietPreference
      ? selectedDiet.dietPreference.charAt(0).toUpperCase() + selectedDiet.dietPreference.slice(1)
      : "Custom";
    return `${prefix} Diet Plan`;
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="text-xl font-semibold text-purple-300 bg-gray-800 px-8 py-4 rounded-lg shadow-lg">
        <span className="inline-block mr-3 animate-spin">⟳</span>
        Loading diet plans...
      </div>
    </div>
  );

  if (error) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="text-xl font-semibold text-red-400 bg-gray-800 px-8 py-4 rounded-lg shadow-lg">
        Error: {error}
      </div>
    </div>
  );

  return (
    <div className="w-full min-h-screen bg-gray-900 text-purple-100 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className={`${instrumentSerif.variable} font-instrument text-5xl text-center mb-8 text-purple-300 pt-6`}>
          Personalized Diet Plans
        </h1>

        {selectedDiet ? (
          <div className="mb-8">
            <button
              onClick={handleBackToList}
              className="mb-6 flex items-center px-4 py-2 bg-gray-800 text-purple-300 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <span className="mr-2">←</span> Back to all diet plans
            </button>

            <div className="mb-6">
              <h2 className="text-3xl font-bold mb-4 text-white capitalize">
                {getSelectedDietTitle()}
              </h2>
              <p className="text-lg text-purple-300 capitalize">{selectedDiet?.goal || "Custom Plan"}</p>
            </div>

            <div className="flex flex-wrap gap-3 mb-6">
              <TabButton active={activeTab === "overview"} onClick={() => setActiveTab("overview")}>Overview</TabButton>
              <TabButton active={activeTab === "plans"} onClick={() => setActiveTab("plans")}>Meal Plans</TabButton>
              <TabButton active={activeTab === "workout"} onClick={() => setActiveTab("workout")}>Workout Routine</TabButton>
            </div>

            <div className="bg-gray-800 rounded-xl shadow-2xl shadow-purple-900/30 p-8 border border-purple-900/50">
              {activeTab === "overview" && (
                <div className="animate-fadeIn">
                  <h2 className="text-3xl font-bold mb-6 text-purple-400 border-b border-purple-800 pb-2">Diet Overview</h2>
                  <div className="grid md:grid-cols-2 gap-8">
                    <div className="bg-gray-900 p-6 rounded-xl shadow-lg border border-purple-800/50">
                      <h3 className="text-xl font-semibold mb-4 text-purple-300">Daily Nutrition Goals</h3>
                      <ul className="space-y-3">
                        <li className="flex justify-between border-b border-gray-700 pb-2">
                          <span>Calories:</span>
                          {console.log("diet is",selectedDiet)}
                          <span className="font-medium text-white">{selectedDiet?.dailyNutrition?.calories} kcal</span>
                        </li>
                        <li className="flex justify-between border-b border-gray-700 pb-2">
                          <span>Carbohydrates:</span>
                          <span className="font-medium text-white">{selectedDiet?.dailyNutrition?.carbs}g</span>
                        </li>
                        <li className="flex justify-between border-b border-gray-700 pb-2">
                          <span>Protein:</span>
                          <span className="font-medium text-white">{selectedDiet?.dailyNutrition?.protein}g</span>
                        </li>
                        <li className="flex justify-between border-b border-gray-700 pb-2">
                          <span>Fats:</span>
                          <span className="font-medium text-white">{selectedDiet?.dailyNutrition?.fats}g</span>
                        </li>
                        <li className="flex justify-between">
                          <span>Water Intake:</span>
                          <span className="font-medium text-white">{selectedDiet?.dailyNutrition?.waterIntake}</span>
                        </li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-xl shadow-lg border border-purple-800/50">
                      <h3 className="text-xl font-semibold mb-4 text-purple-300">Calorie Distribution</h3>
                      <div className="flex flex-col space-y-3">
                        {selectedDiet?.calorieDistribution?.map((item, index) => (
                          <div key={index} className="flex justify-between border-b border-gray-700 pb-2">
                            <span className="capitalize">{item?.category}:</span>
                            <span className="font-medium text-white">{item?.percentage}</span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-6 pt-4 border-t border-gray-700">
                        <div className="flex justify-between mb-3">
                          <span>Diet Preference:</span>
                          <span className="font-medium capitalize text-white">{selectedDiet?.dietPreference}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Goal:</span>
                          <span className="font-medium capitalize text-white">{selectedDiet?.goal || "Not specified"}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "plans" && (
                <div className="animate-fadeIn">
                  <h2 className="text-3xl font-bold mb-6 text-purple-400 border-b border-purple-800 pb-2">Weekly Meal Plan</h2>
                  <div className="space-y-8">
                    {selectedDiet?.mealPlans?.map((dayPlan, dayIndex) => (
                      <div key={dayIndex} className="bg-gray-900 rounded-xl overflow-hidden shadow-lg border border-purple-800/50">
                        <div className="bg-purple-900 p-4">
                          <h3 className="text-2xl font-semibold text-white">{dayPlan?.day}</h3>
                          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm mt-2 text-purple-200">
                            <span>Calories: <strong>{dayPlan?.totalCalories} kcal</strong></span>
                            <span>Carbs: <strong>{dayPlan?.macronutrients?.carbohydrates}g</strong></span>
                            <span>Protein: <strong>{dayPlan?.macronutrients?.proteins}g</strong></span>
                            <span>Fats: <strong>{dayPlan?.macronutrients?.fats}g</strong></span>
                          </div>
                        </div>
                        <div className="p-6">
                          <div className="grid md:grid-cols-3 gap-6">
                            {dayPlan?.meals?.map((meal, mealIndex) => (
                              <div key={mealIndex} className="bg-gray-800 p-4 rounded-lg border border-purple-700/30 shadow-md">
                                <h4 className="text-xl font-medium capitalize mb-3 text-purple-300 border-b border-gray-700 pb-2">{meal?.mealType}</h4>
                                {meal?.items?.map((item, itemIndex) => (
                                  <div key={itemIndex} className="mb-4">
                                    <div className="font-medium text-white">
                                      {item?.name}
                                      <span className="ml-2 text-sm font-normal text-purple-300">({item?.calories} kcal)</span>
                                    </div>
                                    <div className="text-sm text-gray-400 mt-1">
                                      {item?.ingredients?.join(", ")}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === "workout" && (
                <div className="animate-fadeIn">
                  <h2 className="text-3xl font-bold mb-6 text-purple-400 border-b border-purple-800 pb-2">Weekly Workout Routine</h2>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {selectedDiet?.workoutRoutine?.map((day, index) => (
                      <div key={index} className="bg-gray-900 p-5 rounded-xl shadow-lg border border-purple-800/50 hover:border-purple-600 transition-all">
                        <h3 className="text-xl font-semibold mb-3 text-purple-300 border-b border-gray-700 pb-2">{day?.day}</h3>
                        <p className="text-white">{day?.routine}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            <h2 className="text-3xl font-bold mb-8 text-purple-400 border-b border-purple-800 pb-2">Available Diet Plans</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dietsList.length > 0 ? (
                dietsList.map((diet, index) => (
                  <DietCard
                    key={index}
                    diet={diet}
                    onClick={() => handleDietSelect(diet)}
                    index={index}
                  />
                ))
              ) : (
                <div className="col-span-3 text-center py-12 text-gray-400">
                  No diet plans available at the moment.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}