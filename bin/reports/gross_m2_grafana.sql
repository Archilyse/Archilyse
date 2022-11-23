with wall_areas_by_plan as (
    select plans.id as plan_id, separators_area(react_planner_projects.id) from react_planner_projects
    join plans on plans.id = react_planner_projects.plan_id
    join sites on sites.id = plans.site_id
    where site_id = :site_id
), public_area_by_plan as (
    select plans.id as plan_id, sum(ST_AREA(scaled_polygon)) as public_area from areas
        join plans on plans.id = areas.plan_id
        join sites on sites.id = plans.site_id
        where sites.id = :site_id and areas.id not in
        (
            select unit_areas.area_id from unit_areas
                join units on units.id = unit_areas.unit_id
                where units.site_id = :site_id
         )
        group by plans.id
), unit_area_by_plan as (
    select plans.id as plan_id, sum(ST_AREA(scaled_polygon)) as unit_area from areas
        join plans on plans.id = areas.plan_id
        join sites on sites.id = plans.site_id
        where sites.id = :site_id and areas.id in
        (
            select unit_areas.area_id from unit_areas
                join units on units.id = unit_areas.unit_id
                where units.site_id = :site_id
         )
        group by plans.id

), floors_by_plan as (
    select plans.id as plan_id, count(*) as number_of_floors from floors
     join plans on plans.id = floors.plan_id
     group by plans.id
)
select clients.name,
       sites.id as site_id,
       sites.client_site_id,
       wall_areas_by_plan.plan_id,
       ROUND(cast(wall_areas_by_plan.separators_area as numeric), 2) as wall_area,
       ROUND(cast(coalesce(public_area_by_plan.public_area, 0.0) as numeric), 2) as public_area,
       ROUND(cast(coalesce(unit_area_by_plan.unit_area, 0.0) as numeric), 2)  as unit_area,
       ROUND(cast((coalesce(unit_area_by_plan.unit_area, 0.0) + coalesce(public_area_by_plan.public_area, 0.0) + wall_areas_by_plan.separators_area) as numeric), 2) as total_plan_area,
       number_of_floors,
       ROUND(cast(number_of_floors * (coalesce(unit_area_by_plan.unit_area, 0.0) + coalesce(public_area_by_plan.public_area, 0.0) + wall_areas_by_plan.separators_area) as numeric), 2) as total_floor_area,
       extract(year from plans.created) as year_created,
       TO_CHAR(plans.created, 'Month') as month_created,
       DATE_PART('week', plans.created)  as week_created
    from plans
    left join wall_areas_by_plan on wall_areas_by_plan.plan_id = plans.id
    left join public_area_by_plan on public_area_by_plan.plan_id = plans.id
    left join unit_area_by_plan on unit_area_by_plan.plan_id = plans.id
    left join floors_by_plan on floors_by_plan.plan_id = plans.id
    left join sites on sites.id = plans.site_id
    left join clients on clients.id = sites.client_id
    where sites.id = :site_id
    order by plans.id;
