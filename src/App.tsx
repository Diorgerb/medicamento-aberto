import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { CompaniesPage } from './pages/CompaniesPage'
import { CompanyPage } from './pages/CompanyPage'
import { DataPage } from './pages/DataPage'
import { HomePage } from './pages/HomePage'
import { IngredientPage } from './pages/IngredientPage'
import { IngredientsPage } from './pages/IngredientsPage'
import { MedicinesPage } from './pages/MedicinesPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ProductPage } from './pages/ProductPage'
import { TransparencyPage } from './pages/TransparencyPage'
import { UpdatesPage } from './pages/UpdatesPage'
import { ReusePage } from './pages/ReusePage'
import { ViewModeProvider } from './components/ViewModeContext'

export default function App(){
 return <ViewModeProvider><BrowserRouter><Routes><Route element={<Layout/>}><Route path="/" element={<HomePage/>}/><Route path="/medicamentos" element={<MedicinesPage/>}/><Route path="/medicamentos/:id" element={<ProductPage/>}/><Route path="/empresas" element={<CompaniesPage/>}/><Route path="/empresas/:id" element={<CompanyPage/>}/><Route path="/principios-ativos" element={<IngredientsPage/>}/><Route path="/principios-ativos/:id" element={<IngredientPage/>}/><Route path="/sobre" element={<DataPage/>}/><Route path="/dados" element={<Navigate to="/sobre" replace/>}/><Route path="/transparencia" element={<TransparencyPage/>}/><Route path="/atualizacoes" element={<UpdatesPage/>}/><Route path="/reutilize" element={<ReusePage/>}/><Route path="*" element={<NotFoundPage/>}/></Route></Routes></BrowserRouter></ViewModeProvider>
}
