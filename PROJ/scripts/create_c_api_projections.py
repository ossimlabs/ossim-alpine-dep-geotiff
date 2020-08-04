#!/usr/bin/env python
###############################################################################
# $Id$
#
#  Project:  PROJ
#  Purpose:  Parse XML output of Doxygen on coordinateoperation.hpp to creat
#            C API for projections.
#  Author:   Even Rouault <even.rouault at spatialys.com>
#
###############################################################################
#  Copyright (c) 2018, Even Rouault <even.rouault at spatialys.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
###############################################################################

from lxml import etree
import os

script_dir_name = os.path.dirname(os.path.realpath(__file__))

# Make sure to run doxygen
if not 'SKIP_DOXYGEN' in os.environ:
    os.system("bash " + os.path.join(script_dir_name, "doxygen.sh"))

xmlfilename = os.path.join(os.path.dirname(script_dir_name),
        'docs/build/xml/classosgeo_1_1proj_1_1operation_1_1Conversion.xml')

tree = etree.parse(open(xmlfilename, 'rt'))
root = tree.getroot()
compounddef = root.find('compounddef')

header = open('projections.h', 'wt')
cppfile = open('projections.cpp', 'wt')
test_cppfile = open('test_projections.cpp', 'wt')

header.write("/* BEGIN: Generated by scripts/create_c_api_projections.py*/\n")

cppfile.write("/* BEGIN: Generated by scripts/create_c_api_projections.py*/\n")
cppfile.write("\n");

test_cppfile.write("/* BEGIN: Generated by scripts/create_c_api_projections.py*/\n")

def snake_casify(s):
    out = ''
    lastWasLowerAlpha = False
    for c in s:
        if c.isupper():
            if lastWasLowerAlpha:
                out += '_'
            out += c.lower()
            lastWasLowerAlpha = False
        else:
            out += c
            lastWasLowerAlpha = c.isalpha()
    return out


for sectiondef in compounddef.iter('sectiondef'):
    if sectiondef.attrib['kind'] == 'public-static-func':
        for func in sectiondef.iter('memberdef'):
            name = func.find('name').text
            assert name.startswith('create')
            if name in ('create', 'createChangeVerticalUnit',
                        'createAxisOrderReversal', 'createGeographicGeocentric'):
                continue
            params = []
            has_angle = False
            has_linear = False
            for param in func.iter('param'):
                type = param.find('type').xpath("normalize-space()")
                if type.find('Angle') >= 0:
                    has_angle = True
                if type.find('Length') >= 0:
                    has_linear = True
                paramname = param.find('declname').text
                if paramname == 'properties':
                    continue
                params.append((type, snake_casify(paramname)))

            shortName = name[len('create'):]
            c_shortName = snake_casify(shortName)

            decl = "proj_create_conversion_"
            decl += c_shortName
            decl += "(\n"
            decl += "    PJ_CONTEXT *ctx,\n"
            has_output_params = False
            for param in params:
                if has_output_params:
                    decl += ",\n"

                if param[0] in ('int', 'bool'):
                    decl += "    int " + param[1] 
                else:
                    decl += "    double " + param[1]
                has_output_params = True

            if has_angle:
                if has_output_params:
                    decl += ",\n"
                decl += "    const char* ang_unit_name, double ang_unit_conv_factor"
                has_output_params = True
            if has_linear:
                if has_output_params:
                    decl += ",\n"
                decl += "    const char* linear_unit_name, double linear_unit_conv_factor"
            decl += ")"

            header.write("PJ PROJ_DLL *" + decl + ";\n\n")

            briefdescription = func.find('briefdescription/para').xpath("normalize-space()")
            briefdescription = briefdescription.replace("Instanciate ", "Instanciate a ProjectedCRS with ")

            cppfile.write("// ---------------------------------------------------------------------------\n\n")
            cppfile.write("/** \\brief " + briefdescription + "\n")
            cppfile.write(" *\n")
            cppfile.write(" * See osgeo::proj::operation::Conversion::create" + shortName + "().\n")
            cppfile.write(" *\n")
            cppfile.write(" * Linear parameters are expressed in (linear_unit_name, linear_unit_conv_factor).\n")
            if has_angle:
                cppfile.write(" * Angular parameters are expressed in (ang_unit_name, ang_unit_conv_factor).\n")
            cppfile.write(" */\n")
            cppfile.write("PJ* " + decl + "{\n");
            cppfile.write("  SANITIZE_CTX(ctx);\n");
            cppfile.write("  try {\n");
            if has_linear:
                cppfile.write("    UnitOfMeasure linearUnit(createLinearUnit(linear_unit_name, linear_unit_conv_factor));\n")
            if has_angle:
                cppfile.write("    UnitOfMeasure angUnit(createAngularUnit(ang_unit_name, ang_unit_conv_factor));\n")
            cppfile.write("    auto conv = Conversion::create" + shortName + "(PropertyMap()")
            for param in params:
                if param[0] in 'int':
                    cppfile.write(", " + param[1])
                elif param[0] in 'bool':
                    cppfile.write(", " + param[1] + " != 0")
                elif param[0].find('Angle') >= 0:
                    cppfile.write(", Angle(" + param[1] + ", angUnit)")
                elif param[0].find('Length') >= 0:
                    cppfile.write(", Length(" + param[1] + ", linearUnit)")
                elif param[0].find('Scale') >= 0:
                    cppfile.write(", Scale(" + param[1] + ")")

            cppfile.write(");\n")
            cppfile.write("    return proj_create_conversion(conv);\n")
            cppfile.write("  } catch (const std::exception &e) {\n");
            cppfile.write("    proj_log_error(ctx, __FUNCTION__, e.what());\n")
            cppfile.write("  }\n")
            cppfile.write("  return nullptr;\n")
            cppfile.write("}\n")

            test_cppfile.write("{\n")
            test_cppfile.write("    auto projCRS = proj_create_conversion_" + c_shortName + "(\n")
            test_cppfile.write("        m_ctxt")
            for param in params:
                test_cppfile.write(", 0")
            if has_angle:
                test_cppfile.write(", \"Degree\", 0.0174532925199433")
            if has_angle:
                test_cppfile.write(", \"Metre\", 1.0")
            test_cppfile.write(");\n")
            test_cppfile.write("    ObjectKeeper keeper_projCRS(projCRS);\n")
            test_cppfile.write("    ASSERT_NE(projCRS, nullptr);\n")
            test_cppfile.write("}\n")


header.write("/* END: Generated by scripts/create_c_api_projections.py*/\n")
cppfile.write("/* END: Generated by scripts/create_c_api_projections.py*/\n")

test_cppfile.write("/* END: Generated by scripts/create_c_api_projections.py*/\n")

print('projections.h and .cpp, and test_projections.cpp have been generated. Manually merge them now')