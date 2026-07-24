-- CreateEnum
CREATE TYPE "OrgRole" AS ENUM ('OWNER', 'ADMIN', 'MEMBER', 'VIEWER');

-- CreateEnum
CREATE TYPE "MateType" AS ENUM ('FIXED', 'REVOLUTE', 'SLIDER', 'CYLINDRICAL', 'PLANAR', 'BALL', 'PARALLEL', 'COINCIDENT');

-- CreateEnum
CREATE TYPE "AnalysisKind" AS ENUM ('FEA_LINEAR_STATIC', 'CALC_BOLT', 'CALC_BEAM', 'CALC_GEAR', 'CALC_SPRING', 'CALC_SHAFT', 'CALC_BEARING', 'CALC_TOLERANCE', 'MASS_PROPERTIES', 'WALL_THICKNESS', 'PRINTABILITY');

-- CreateEnum
CREATE TYPE "Slicer" AS ENUM ('FLASHPRINT', 'ORCASLICER', 'PRUSASLICER', 'CURA', 'BAMBU_STUDIO');

-- CreateEnum
CREATE TYPE "PrintStatus" AS ENUM ('DRAFT', 'QUEUED', 'PRINTING', 'COMPLETED', 'FAILED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "AssetKind" AS ENUM ('STL', 'OBJ', 'THREE_MF', 'STEP', 'IGES', 'GLB', 'PLY', 'FBX', 'DXF', 'SVG', 'RENDER', 'THUMBNAIL', 'PDF', 'BLEND');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "authId" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "displayName" TEXT,
    "preferences" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Organization" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Organization_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Membership" (
    "id" TEXT NOT NULL,
    "role" "OrgRole" NOT NULL DEFAULT 'MEMBER',
    "userId" TEXT NOT NULL,
    "orgId" TEXT NOT NULL,

    CONSTRAINT "Membership_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Project" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "ownerId" TEXT NOT NULL,
    "orgId" TEXT,
    "headVersionId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ProjectVersion" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "message" TEXT,
    "parentId" TEXT,
    "createdById" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ProjectVersion_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Part" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "headVersionId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Part_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PartVersion" (
    "id" TEXT NOT NULL,
    "partId" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "parentId" TEXT,
    "featureProgram" JSONB NOT NULL,
    "paramTableCache" JSONB,
    "massG" DOUBLE PRECISION,
    "volumeMm3" DOUBLE PRECISION,
    "bboxJson" JSONB,
    "createdById" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PartVersion_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Material" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "isSystem" BOOLEAN NOT NULL DEFAULT false,
    "ownerId" TEXT,
    "orgId" TEXT,
    "densityGCm3" DOUBLE PRECISION NOT NULL,
    "youngsModulusMPa" DOUBLE PRECISION,
    "yieldStrengthMPa" DOUBLE PRECISION,
    "tensileStrengthMPa" DOUBLE PRECISION,
    "elongationPct" DOUBLE PRECISION,
    "shrinkagePct" DOUBLE PRECISION,
    "printTempC" INTEGER,
    "bedTempC" INTEGER,
    "costPerKg" DOUBLE PRECISION,
    "colorHex" TEXT DEFAULT '#B0B0B0',
    "solubleSupport" BOOLEAN NOT NULL DEFAULT false,
    "meta" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Material_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MaterialAssignment" (
    "id" TEXT NOT NULL,
    "partVersionId" TEXT NOT NULL,
    "bodyRef" TEXT NOT NULL,
    "materialId" TEXT NOT NULL,
    "colorHex" TEXT,
    "role" TEXT,

    CONSTRAINT "MaterialAssignment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Assembly" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Assembly_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AssemblyNode" (
    "id" TEXT NOT NULL,
    "assemblyId" TEXT NOT NULL,
    "parentId" TEXT,
    "partId" TEXT,
    "name" TEXT NOT NULL,
    "transform" JSONB NOT NULL DEFAULT '{}',

    CONSTRAINT "AssemblyNode_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Mate" (
    "id" TEXT NOT NULL,
    "type" "MateType" NOT NULL,
    "nodeAId" TEXT NOT NULL,
    "nodeBId" TEXT NOT NULL,
    "params" JSONB NOT NULL DEFAULT '{}',

    CONSTRAINT "Mate_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Analysis" (
    "id" TEXT NOT NULL,
    "partVersionId" TEXT NOT NULL,
    "kind" "AnalysisKind" NOT NULL,
    "inputsHash" TEXT NOT NULL,
    "inputs" JSONB NOT NULL,
    "result" JSONB NOT NULL,
    "advisory" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Analysis_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PrintProfile" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "slicer" "Slicer" NOT NULL,
    "settings" JSONB NOT NULL,
    "ownerId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PrintProfile_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PrintJob" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "profileId" TEXT,
    "status" "PrintStatus" NOT NULL DEFAULT 'DRAFT',
    "estMaterialG" DOUBLE PRECISION,
    "actMaterialG" DOUBLE PRECISION,
    "estMinutes" INTEGER,
    "actMinutes" INTEGER,
    "estCost" DOUBLE PRECISION,
    "actCost" DOUBLE PRECISION,
    "materialsJson" JSONB,
    "purgeG" DOUBLE PRECISION,
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "PrintJob_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Bom" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Bom_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BomItem" (
    "id" TEXT NOT NULL,
    "bomId" TEXT NOT NULL,
    "reference" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "quantity" DOUBLE PRECISION NOT NULL DEFAULT 1,
    "unit" TEXT NOT NULL DEFAULT 'ea',
    "unitCost" DOUBLE PRECISION,
    "partId" TEXT,
    "fastenerId" TEXT,
    "materialId" TEXT,

    CONSTRAINT "BomItem_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Drawing" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "sheetSize" TEXT NOT NULL DEFAULT 'A3',
    "revision" TEXT NOT NULL DEFAULT 'A',
    "pdfAssetId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Drawing_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Fastener" (
    "id" TEXT NOT NULL,
    "standard" TEXT NOT NULL,
    "size" TEXT NOT NULL,
    "grade" TEXT,
    "meta" JSONB NOT NULL DEFAULT '{}',

    CONSTRAINT "Fastener_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Asset" (
    "id" TEXT NOT NULL,
    "ownerId" TEXT NOT NULL,
    "projectId" TEXT,
    "partVersionId" TEXT,
    "kind" "AssetKind" NOT NULL,
    "storageBucket" TEXT NOT NULL DEFAULT 'efproj',
    "storageKey" TEXT NOT NULL,
    "contentType" TEXT NOT NULL,
    "sizeBytes" INTEGER NOT NULL,
    "checksum" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Asset_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditLog" (
    "id" TEXT NOT NULL,
    "actorId" TEXT,
    "action" TEXT NOT NULL,
    "target" TEXT,
    "meta" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_authId_key" ON "User"("authId");

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE INDEX "Membership_orgId_idx" ON "Membership"("orgId");

-- CreateIndex
CREATE UNIQUE INDEX "Membership_userId_orgId_key" ON "Membership"("userId", "orgId");

-- CreateIndex
CREATE UNIQUE INDEX "Project_headVersionId_key" ON "Project"("headVersionId");

-- CreateIndex
CREATE INDEX "Project_ownerId_updatedAt_idx" ON "Project"("ownerId", "updatedAt");

-- CreateIndex
CREATE INDEX "Project_orgId_idx" ON "Project"("orgId");

-- CreateIndex
CREATE INDEX "ProjectVersion_projectId_createdAt_idx" ON "ProjectVersion"("projectId", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "Part_headVersionId_key" ON "Part"("headVersionId");

-- CreateIndex
CREATE INDEX "Part_projectId_idx" ON "Part"("projectId");

-- CreateIndex
CREATE INDEX "PartVersion_partId_createdAt_idx" ON "PartVersion"("partId", "createdAt");

-- CreateIndex
CREATE INDEX "Material_ownerId_idx" ON "Material"("ownerId");

-- CreateIndex
CREATE INDEX "Material_isSystem_idx" ON "Material"("isSystem");

-- CreateIndex
CREATE INDEX "MaterialAssignment_materialId_idx" ON "MaterialAssignment"("materialId");

-- CreateIndex
CREATE UNIQUE INDEX "MaterialAssignment_partVersionId_bodyRef_key" ON "MaterialAssignment"("partVersionId", "bodyRef");

-- CreateIndex
CREATE INDEX "Assembly_projectId_idx" ON "Assembly"("projectId");

-- CreateIndex
CREATE INDEX "AssemblyNode_assemblyId_idx" ON "AssemblyNode"("assemblyId");

-- CreateIndex
CREATE INDEX "AssemblyNode_parentId_idx" ON "AssemblyNode"("parentId");

-- CreateIndex
CREATE INDEX "Mate_nodeAId_idx" ON "Mate"("nodeAId");

-- CreateIndex
CREATE INDEX "Mate_nodeBId_idx" ON "Mate"("nodeBId");

-- CreateIndex
CREATE INDEX "Analysis_partVersionId_idx" ON "Analysis"("partVersionId");

-- CreateIndex
CREATE UNIQUE INDEX "Analysis_partVersionId_kind_inputsHash_key" ON "Analysis"("partVersionId", "kind", "inputsHash");

-- CreateIndex
CREATE INDEX "PrintJob_projectId_createdAt_idx" ON "PrintJob"("projectId", "createdAt");

-- CreateIndex
CREATE INDEX "Bom_projectId_idx" ON "Bom"("projectId");

-- CreateIndex
CREATE INDEX "BomItem_bomId_idx" ON "BomItem"("bomId");

-- CreateIndex
CREATE INDEX "Drawing_projectId_idx" ON "Drawing"("projectId");

-- CreateIndex
CREATE UNIQUE INDEX "Fastener_standard_size_grade_key" ON "Fastener"("standard", "size", "grade");

-- CreateIndex
CREATE UNIQUE INDEX "Asset_storageKey_key" ON "Asset"("storageKey");

-- CreateIndex
CREATE INDEX "Asset_ownerId_kind_idx" ON "Asset"("ownerId", "kind");

-- CreateIndex
CREATE INDEX "Asset_projectId_idx" ON "Asset"("projectId");

-- CreateIndex
CREATE INDEX "AuditLog_actorId_createdAt_idx" ON "AuditLog"("actorId", "createdAt");

-- AddForeignKey
ALTER TABLE "Membership" ADD CONSTRAINT "Membership_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Membership" ADD CONSTRAINT "Membership_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Organization"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_headVersionId_fkey" FOREIGN KEY ("headVersionId") REFERENCES "ProjectVersion"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectVersion" ADD CONSTRAINT "ProjectVersion_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Part" ADD CONSTRAINT "Part_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Part" ADD CONSTRAINT "Part_headVersionId_fkey" FOREIGN KEY ("headVersionId") REFERENCES "PartVersion"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PartVersion" ADD CONSTRAINT "PartVersion_partId_fkey" FOREIGN KEY ("partId") REFERENCES "Part"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Material" ADD CONSTRAINT "Material_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Material" ADD CONSTRAINT "Material_orgId_fkey" FOREIGN KEY ("orgId") REFERENCES "Organization"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MaterialAssignment" ADD CONSTRAINT "MaterialAssignment_partVersionId_fkey" FOREIGN KEY ("partVersionId") REFERENCES "PartVersion"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MaterialAssignment" ADD CONSTRAINT "MaterialAssignment_materialId_fkey" FOREIGN KEY ("materialId") REFERENCES "Material"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Assembly" ADD CONSTRAINT "Assembly_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AssemblyNode" ADD CONSTRAINT "AssemblyNode_assemblyId_fkey" FOREIGN KEY ("assemblyId") REFERENCES "Assembly"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AssemblyNode" ADD CONSTRAINT "AssemblyNode_parentId_fkey" FOREIGN KEY ("parentId") REFERENCES "AssemblyNode"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Mate" ADD CONSTRAINT "Mate_nodeAId_fkey" FOREIGN KEY ("nodeAId") REFERENCES "AssemblyNode"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Mate" ADD CONSTRAINT "Mate_nodeBId_fkey" FOREIGN KEY ("nodeBId") REFERENCES "AssemblyNode"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Analysis" ADD CONSTRAINT "Analysis_partVersionId_fkey" FOREIGN KEY ("partVersionId") REFERENCES "PartVersion"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PrintJob" ADD CONSTRAINT "PrintJob_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PrintJob" ADD CONSTRAINT "PrintJob_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "PrintProfile"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Bom" ADD CONSTRAINT "Bom_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BomItem" ADD CONSTRAINT "BomItem_bomId_fkey" FOREIGN KEY ("bomId") REFERENCES "Bom"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Drawing" ADD CONSTRAINT "Drawing_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Asset" ADD CONSTRAINT "Asset_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Asset" ADD CONSTRAINT "Asset_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Asset" ADD CONSTRAINT "Asset_partVersionId_fkey" FOREIGN KEY ("partVersionId") REFERENCES "PartVersion"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditLog" ADD CONSTRAINT "AuditLog_actorId_fkey" FOREIGN KEY ("actorId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

