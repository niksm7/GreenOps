def get_summary_report_data():
    data = """
    1. Executive Summary
    Total estimated monthly cost savings from optimization: Approximately $1163.84 (Note: Some values not available due to pricing error.)
    Total estimated monthly carbon reductions from optimization: Approximately 1471.87 kgCO2e (Note: Some values not available due to pricing error.)
    Forecast: Carbon emissions are projected to increase slightly over the next 7 days.
    Regions Analyzed: 5

    2. Regional Highlights

    Asia South 1
    Count of underutilized instances: 2
    Average CPU Utilization: Varies, see instance details below
    Average Memory Utilization: Varies, see instance details below
    Instances with highest carbon emissions: b6e68e26-65fb-4bf3-978a-3412b35b6b4a (2.26 kg), a9e82a31-6847-4b9b-a5e5-02f273b2927a (1.365 kg)

    Europe West 1
    Count of underutilized instances: 2
    Average CPU Utilization: Varies, see instance details below
    Average Memory Utilization: Varies, see instance details below
    Instances with highest carbon emissions: efa620b7-42c6-4b83-bc95-84e6a01a531b (2.36 kg), 3451da66-9dea-430f-8425-52cca5b94fda (2.449 kg)

    US Central 1
    Count of underutilized instances: 2
    Average CPU Utilization: Varies, see instance details below
    Average Memory Utilization: Varies, see instance details below
    Instances with highest carbon emissions: 8f587811-b8a1-47da-9f58-20b59432847a (2.726 kg), 50bec138-4007-448c-b136-5f0136795fe5 (1.478 kg)

    US East 1
    Count of underutilized instances: 2
    Average CPU Utilization: Varies, see instance details below
    Average Memory Utilization: Varies, see instance details below
    Instances with highest carbon emissions: c5ae3b87-3c83-47a3-8c84-1c7089f613bc (0.699 kg), f47efcac-8d9c-4adf-88f7-9bd84f6da753 (0.785 kg)

    US West 1
    Count of underutilized instances: 2
    Average CPU Utilization: Varies, see instance details below
    Average Memory Utilization: Varies, see instance details below
    Instances with highest carbon emissions: b502ff42-b413-46b6-8c36-2372a82b93ab (1.986 kg), 704aa8df-20cd-4caf-be43-91deb403d437 (1.91 kg)

    3. Overall Carbon Forecast Analysis

    Projected total emission for next 7 days: 96.663 kg
    Date with highest projected emission: 2025-06-27 (16.012 kg)
    Top carbon-emitting instances: b6e68e26-65fb-4bf3-978a-3412b35b6b4a (8.311 kg), 704aa8df-20cd-4caf-be43-91deb403d437 (7.525 kg)

    4. Optimization Recommendations

    Asia South 1
    Infrastructure Recommendations for asia_south_1

    Summary
    Based on the analysis, there are opportunities to optimize resource utilization in the asia_south_1 region. Several instances are underutilized in terms of CPU and memory, suggesting potential cost and carbon emission savings through downgrading to smaller instance types.

    Detailed Recommendations:

    Instance ID: 30ab5043-5bf1-49ca-806d-fe6373abb1e3
    Issue Identified: CPU underutilized at 10.26%, Memory at 38.93%
    Current Instance Type: e2-standard-8
    Recommendation: Downgrade to e2-standard-4 to reduce costs and carbon emissions due to low CPU utilization.
    Potential savings based on current and target instance:
    Cost Savings/Month: $115.89
    Carbon Savings/Month: 300.24 kg


    Instance ID: 9334f0c2-419a-4e77-a623-135e76e7ae28
    Issue Identified: CPU underutilized at 20.73%, Memory at 21.47%
    Current Instance Type: e2-highmem-8
    Recommendation: Downgrade to e2-highmem-4 due to low CPU and Memory utilization.
    Potential savings based on current and target instance:
    Cost Savings/Month: $156.34
    Carbon Savings/Month: 464.66 kg


    Europe West 1
    Infrastructure Recommendations for europe_west_1
    Summary
    Two optimization opportunities were identified in the europe_west_1 region. One instance of type `a2-highgpu-1g` and one instance of type `e2-standard-8` are heavily underutilized. Recommendations include migrating to smaller instance types to reduce costs and carbon emissions.

    Detailed Recommendations:

    Instance ID: `a666158d-7dbf-497e-be47-a4cd69ad7ded`
    Issue Identified: CPU underutilized at 10.03%, Memory at 17.74%
    Current Instance Type: `e2-standard-8`
    Recommendation: Downsize to `e2-standard-4`. The instance has very low CPU usage, so a smaller instance will suffice.
    Potential savings:
    Cost Savings/Month: $106.15
    Carbon Savings/Month: 143.71 kg


    US Central 1
    Infrastructure Recommendations for us_central_1

    Summary
    This report identifies underutilized instances in the `us_central_1` region and suggests instance downgrades to optimize resource utilization, reduce costs, and lower carbon emissions.

    Detailed Recommendations:

    Instance ID: `instance-20250614-105928`
    Issue Identified: CPU underutilized at 5.6%, Memory at 17.98%
    Current Instance Type: `e2-medium`
    Recommendation: Downgrade to `e2-micro` due to severe underutilization.
    Potential Savings:
    Cost Savings/Month: $6.31
    Carbon Savings/Month: 10.15 gCO2e


    Instance ID: `50bec138-4007-448c-b136-5f0136795fe5`
    Issue Identified: CPU underutilized at 22.19%, Memory at 29.47%
    Current Instance Type: `e2-highcpu-4`
    Recommendation: Downgrade to `e2-highcpu-2` as CPU usage is very low.
    Potential Savings:
    Cost Savings/Month: $35.62
    Carbon Savings/Month: 84.67 gCO2e


    US East 1
    Infrastructure Recommendations for us_east_1

    Summary
    The analysis identified two instances in the us_east_1 region with significant underutilization of CPU and memory resources. Recommendations are provided to downgrade these instances to smaller sizes, resulting in potential cost and carbon emission savings.

    Detailed Recommendations:
    Instance ID: 109763a1-c2a0-4b89-b013-7784efeca87c
    Issue Identified: CPU underutilized at 8.8%, Memory at 10.09%
    Current Instance Type: n1-highmem-4
    Recommendation: Downgrade to n1-highmem-2 due to very low CPU and memory utilization.
    Potential Savings:
    Cost Savings/Month: $85.18
    Carbon Savings/Month: 113.11 kg


    Instance ID: f2050170-0296-471b-b12f-08987dbf75d4
    Issue Identified: CPU underutilized at 8.67%, Memory at 14.64%
    Current Instance Type: n1-standard-8
    Recommendation: Downgrade to n1-standard-4 due to extremely low CPU and memory utilization.
    Potential Savings:
    Cost Savings/Month: $136.8
    Carbon Savings/Month: 179.93 kg


    US West 1
    Infrastructure Recommendations for us_west_1
    Summary
    Based on the analysis of the provided data, several instances in the `us_west_1` region are underutilized. This report provides recommendations to optimize instance sizes, reduce costs, and lower carbon emissions.

    Detailed Recommendations:
    Instance ID: 641f7096-e9db-4c1d-a92e-fea3ea89f35d
    Issue Identified: CPU underutilized at 10.17%, Memory at 32.14%
    Current Instance Type: a2-highgpu-1g
    Recommendation: Downgrade to e2-medium. This will provide a more appropriately sized instance based on the observed low utilization.
    Potential savings based on current and target instance:
    Cost Savings/Month: $492.53
    Carbon Savings/Month: 385.93 gCO2e


    Instance ID: f11ccce0-adf6-4d01-b110-65c5a093cb9e
    Issue Identified: CPU underutilized at 21.91%, Memory at 11.33%
    Current Instance Type: e2-highmem-8
    Recommendation: Downgrade to e2-highmem-4. The instance is significantly underutilized, and this change will better align resources with actual usage.
    Potential savings based on current and target instance:
    Cost Savings/Month: $129.60
    Carbon Savings/Month: 190.08 gCO2e



    5. Instance Behavior Analysis
    As per the data:
    Instance types a2-highgpu-1g and a2-highgpu-4g generally emit higher carbon per CPU.
    Instances with low CPU utilization but high carbon emissions were observed, indicating potential areas for optimization.
    """
    
    return data